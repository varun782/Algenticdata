from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class MigrationPlan(Base):
    __tablename__ = 'migration_plans'
    id = Column(Integer, primary_key=True, index=True)
    version = Column(Integer, default=1)
    status = Column(String, default="draft") # draft, approved, executed
    source_schema = Column(JSON)
    target_schema = Column(JSON)
    mappings = Column(JSON) # AI generated mappings
    risks = Column(JSON)
    questions = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)
    executions = relationship("ExecutionLog", back_populates="plan")

class ExecutionLog(Base):
    __tablename__ = 'execution_logs'
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("migration_plans.id"))
    status = Column(String, default="dry_run") # dry_run, executed, rolled_back
    source_count = Column(Integer, default=0)
    transformed_count = Column(Integer, default=0)
    accepted_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    plan = relationship("MigrationPlan", back_populates="executions")
    quarantine_records = relationship("QuarantineRecord", back_populates="execution", cascade="all, delete-orphan")
    target_records = relationship("MockTargetData", back_populates="execution", cascade="all, delete-orphan")

class QuarantineRecord(Base):
    __tablename__ = 'quarantine_records'
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("execution_logs.id"))
    source_record_id = Column(String)
    original_data = Column(JSON)
    errors = Column(JSON) # Field level errors e.g. {"email": "invalid format"}
    execution = relationship("ExecutionLog", back_populates="quarantine_records")

class MockTargetData(Base):
    __tablename__ = 'mock_target_data'
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("execution_logs.id"))
    source_record_id = Column(String, unique=True, index=True) # Prevent duplicates across executions
    data = Column(JSON)
    execution = relationship("ExecutionLog", back_populates="target_records")
