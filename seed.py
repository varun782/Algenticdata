import json
from database import engine
import models
import models

# Recreate DB tables
models.Base.metadata.create_all(bind=engine)

SOURCE_SCHEMA = {
    "type": "object",
    "properties": {
        "customer_id": {"type": "string"},
        "full_name": {"type": "string"},
        "email_address": {"type": "string"},
        "signup_date": {"type": "string"}, # Format: YYYY-MM-DD
        "zip_code": {"type": "string"}
    }
}

TARGET_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "email": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "postal_code": {"type": "string"},
        "status": {"type": "string"} # default to "active"
    },
    "required": ["id", "email", "created_at", "status"]
}

SAMPLE_RECORDS = [
    {"customer_id": "C100", "full_name": "Alice Smith", "email_address": "alice@example.com", "signup_date": "2023-01-15", "zip_code": "10001"},
    {"customer_id": "C101", "full_name": "Bob Jones", "email_address": "bob.jones@test.com", "signup_date": "2023-02-20", "zip_code": "90210"},
    {"customer_id": "C102", "full_name": "Charlie", "email_address": "invalid-email", "signup_date": "2023-03-05", "zip_code": "02134"}
]

TRANSFORMATION_RULES = [
    "split_name_to_first_and_last(full_name)",
    "parse_date_to_iso8601(date_string)",
    "lowercase(string)",
    "uppercase(string)",
    "default_value(value)",
    "map_direct(source_field, target_field)"
]

print("Database and mock data initialized.")
