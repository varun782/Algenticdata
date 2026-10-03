import os
from google import genai
from dotenv import load_dotenv
from typing import List, Dict, Any
from schemas import AgentMigrationPlan

load_dotenv()

# Initialize Gemini Client
# Assumes GEMINI_API_KEY is set in environment or .env
client = genai.Client()

def generate_migration_plan(source_schema: Dict[str, Any], target_schema: Dict[str, Any], sample_records: List[Dict[str, Any]], rules: List[str]) -> AgentMigrationPlan:
    prompt = f"""
    You are an expert data migration architect.
    Your task is to propose a migration plan to move data from a SOURCE SCHEMA to a TARGET SCHEMA.
    
    SOURCE SCHEMA:
    {source_schema}
    
    TARGET SCHEMA:
    {target_schema}
    
    SAMPLE SOURCE RECORDS:
    {sample_records}
    
    SUPPORTED TRANSFORMATION RULES:
    {rules}
    
    Analyze the schemas and propose field mappings. Identify missing fields, incompatibilities, and risks.
    Generate clarification questions if any fields are ambiguous.
    Output the plan as structured JSON matching the provided schema.
    """
    
    import time
    from google.genai.errors import APIError
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AgentMigrationPlan,
                ),
            )
            return AgentMigrationPlan.model_validate_json(response.text)
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise e
