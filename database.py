from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os

if os.environ.get("VERCEL"):
    SQLALCHEMY_DATABASE_URL = "sqlite:////tmp/migration.db"
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./migration.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
