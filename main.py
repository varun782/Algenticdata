from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, engine
import models
import schemas
import agent
import seed
from datetime import datetime, timezone
import json
import uuid
import os

app = FastAPI(title="Migration Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=engine)
    os.makedirs("static", exist_ok=True)

@app.get("/api/schemas")
def get_schemas():
    return {
        "source_schema": seed.SOURCE_SCHEMA,
        "target_schema": seed.TARGET_SCHEMA,
        "sample_records": seed.SAMPLE_RECORDS,
        "rules": seed.TRANSFORMATION_RULES
    }

@app.post("/api/plan/generate")
def generate_plan(db: Session = Depends(get_db)):
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing. Please set it in the .env file.")
        
    try:
        agent_plan = agent.generate_migration_plan(
            seed.SOURCE_SCHEMA,
            seed.TARGET_SCHEMA,
            seed.SAMPLE_RECORDS,
            seed.TRANSFORMATION_RULES
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    db_plan = models.MigrationPlan(
        source_schema=seed.SOURCE_SCHEMA,
        target_schema=seed.TARGET_SCHEMA,
        mappings=[m.model_dump() for m in agent_plan.mappings],
        risks=agent_plan.risks,
        questions=agent_plan.clarification_questions,
        status="draft"
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@app.get("/api/plan/{plan_id}")
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.MigrationPlan).filter(models.MigrationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@app.get("/api/plans")
def get_plans(db: Session = Depends(get_db)):
    plans = db.query(models.MigrationPlan).order_by(models.MigrationPlan.id.desc()).all()
    return plans

@app.post("/api/plan/{plan_id}/approve")
def approve_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.MigrationPlan).filter(models.MigrationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status != "draft":
        raise HTTPException(status_code=400, detail="Plan must be in draft status to approve")
    
    plan.status = "approved"
    plan.approved_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Plan approved"}

def _apply_transformation(val, transformation_rule):
    if not val:
        return val
    if transformation_rule == "split_name_to_first_and_last(full_name)":
        return val 
    elif transformation_rule == "parse_date_to_iso8601(date_string)":
        try:
            return datetime.strptime(val, "%Y-%m-%d").isoformat()
        except:
            raise ValueError(f"Invalid date format: {val}")
    elif transformation_rule == "lowercase(string)":
        return str(val).lower()
    elif transformation_rule == "uppercase(string)":
        return str(val).upper()
    elif transformation_rule == "default_value(value)":
        return val
    elif transformation_rule == "map_direct(source_field, target_field)":
        return val
    return val

@app.post("/api/plan/{plan_id}/dry_run")
def dry_run_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.MigrationPlan).filter(models.MigrationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    execution = models.ExecutionLog(plan_id=plan.id, status="dry_run", source_count=len(seed.SAMPLE_RECORDS))
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    accepted = 0
    rejected = 0
    transformed = 0
    
    for record in seed.SAMPLE_RECORDS:
        target_record = {}
        errors = {}
        
        target_record['id'] = record.get('customer_id') or str(uuid.uuid4())
        
        for mapping in plan.mappings:
            source_field = mapping.get('source_field')
            target_field = mapping.get('target_field')
            rule = mapping.get('transformation')
            
            if source_field == "full_name" and rule == "split_name_to_first_and_last(full_name)":
                parts = record.get("full_name", "").split(" ", 1)
                if target_field == "first_name":
                    target_record["first_name"] = parts[0] if len(parts) > 0 else ""
                elif target_field == "last_name":
                    target_record["last_name"] = parts[1] if len(parts) > 1 else ""
                continue
                
            val = record.get(source_field)
            if val is not None:
                try:
                    target_record[target_field] = _apply_transformation(val, rule)
                except Exception as e:
                    errors[source_field] = str(e)
                    
        if "status" not in target_record:
            target_record["status"] = "active"
            
        for req in seed.TARGET_SCHEMA.get("required", []):
            if req not in target_record or not target_record[req]:
                errors[req] = "Missing required field"
                
        if errors:
            rejected += 1
            qr = models.QuarantineRecord(
                execution_id=execution.id,
                source_record_id=record.get("customer_id", "unknown"),
                original_data=record,
                errors=errors
            )
            db.add(qr)
        else:
            accepted += 1
            transformed += 1
            
    execution.transformed_count = transformed
    execution.accepted_count = accepted
    execution.rejected_count = rejected
    db.commit()
    
    return {
        "execution_id": execution.id,
        "counts": {
            "source": execution.source_count,
            "accepted": execution.accepted_count,
            "rejected": execution.rejected_count
        }
    }

@app.post("/api/plan/{plan_id}/execute")
def execute_plan(plan_id: int, execution_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.MigrationPlan).filter(models.MigrationPlan.id == plan_id).first()
    if not plan or plan.status != "approved":
        raise HTTPException(status_code=400, detail="Plan must be approved to execute")
        
    execution = db.query(models.ExecutionLog).filter(models.ExecutionLog.id == execution_id).first()
    if not execution or execution.status != "dry_run":
        raise HTTPException(status_code=400, detail="Must provide a valid dry run execution ID")
    
    accepted = 0
    rejected = 0
    transformed = 0
    
    for record in seed.SAMPLE_RECORDS:
        target_record = {}
        errors = {}
        
        target_record['id'] = record.get('customer_id') or str(uuid.uuid4())
        
        for mapping in plan.mappings:
            source_field = mapping.get('source_field')
            target_field = mapping.get('target_field')
            rule = mapping.get('transformation')
            
            if source_field == "full_name" and rule == "split_name_to_first_and_last(full_name)":
                parts = record.get("full_name", "").split(" ", 1)
                if target_field == "first_name":
                    target_record["first_name"] = parts[0] if len(parts) > 0 else ""
                elif target_field == "last_name":
                    target_record["last_name"] = parts[1] if len(parts) > 1 else ""
                continue
                
            val = record.get(source_field)
            if val is not None:
                try:
                    target_record[target_field] = _apply_transformation(val, rule)
                except Exception as e:
                    errors[source_field] = str(e)
                    
        if "status" not in target_record:
            target_record["status"] = "active"
            
        for req in seed.TARGET_SCHEMA.get("required", []):
            if req not in target_record or not target_record[req]:
                errors[req] = "Missing required field"
                
        if not errors:
            existing = db.query(models.MockTargetData).filter(models.MockTargetData.source_record_id == target_record['id']).first()
            if not existing:
                mock_target = models.MockTargetData(
                    execution_id=execution.id,
                    source_record_id=target_record['id'],
                    data=target_record
                )
                db.add(mock_target)
                accepted += 1
            else:
                rejected += 1 # duplicate
        else:
            rejected += 1
            
    execution.status = "executed"
    execution.accepted_count = accepted
    db.commit()
    
    return {"message": f"Execution complete. Inserted {accepted} records.", "execution_id": execution.id}

@app.post("/api/execution/{execution_id}/rollback")
def rollback_execution(execution_id: int, db: Session = Depends(get_db)):
    execution = db.query(models.ExecutionLog).filter(models.ExecutionLog.id == execution_id).first()
    if not execution or execution.status != "executed":
        raise HTTPException(status_code=400, detail="Only executed migrations can be rolled back")
        
    db.query(models.MockTargetData).filter(models.MockTargetData.execution_id == execution.id).delete()
    execution.status = "rolled_back"
    db.commit()
    return {"message": "Rollback successful"}

@app.get("/api/reconciliation")
def get_reconciliation(db: Session = Depends(get_db)):
    executions = db.query(models.ExecutionLog).order_by(models.ExecutionLog.id.desc()).all()
    target_records = db.query(models.MockTargetData).count()
    return {
        "executions": executions,
        "target_total": target_records,
        "source_total": len(seed.SAMPLE_RECORDS)
    }

app.mount("/", StaticFiles(directory="static", html=True), name="static")

