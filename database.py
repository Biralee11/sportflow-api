from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Creates the connection to the PostgreSQL database
engine = create_engine(DATABASE_URL)

# Factory for creating database sessions. autocommit=False means changes must be
# explicitly committed. autoflush=False prevents automatic syncing before queries.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class that all database models inherit from.
# SQLAlchemy uses this to track and map models to database tables.
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
