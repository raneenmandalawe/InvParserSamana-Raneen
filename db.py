"""
Database connection and session management using SQLAlchemy.

Supports both SQLite and PostgreSQL based on DB_BACKEND environment variable.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Determine database backend from environment variable
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")

# Configure database URL based on backend
if DB_BACKEND == "postgres":
    POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pass")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "predictions")
    
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    # Default to SQLite
    DATABASE_URL = "sqlite:///./invoices.db"

# Create engine with appropriate settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database schema.
    
    Creates all tables defined in models.
    """
    # Import models to register them with Base
    import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)


def clean_db():
    """
    Clean the database by dropping all tables.
    
    Used for testing purposes.
    """
    Base.metadata.drop_all(bind=engine)
