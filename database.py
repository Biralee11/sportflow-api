from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

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
