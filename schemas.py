from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class FieldMapping(BaseModel):
    source_field: str
    target_field: str
    transformation: Optional[str] = None
    confidence: str # e.g., 'High', 'Medium', 'Low'
    reasoning: str

class AgentMigrationPlan(BaseModel):
    mappings: List[FieldMapping]
    incompatible_fields: List[str]
    missing_target_fields: List[str]
    risks: List[str]
    clarification_questions: List[str]
    summary: str
