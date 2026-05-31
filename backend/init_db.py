"""
Standalone script — drops and recreates all database tables.

Safe to run multiple times. Always produces a schema that exactly matches
the current SQLAlchemy models. Use freely during development; do not run
against a database with real data you need to keep.

    cd backend
    python init_db.py
"""

from database import Base, engine
import models  # noqa: F401 — registers all ORM classes with Base.metadata

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Database recreated successfully.")
print("Tables:", list(Base.metadata.tables.keys()))

# Print columns for devices table so schema can be verified at a glance
from sqlalchemy import inspect as sa_inspect
inspector = sa_inspect(engine)
cols = [c["name"] for c in inspector.get_columns("devices")]
print("devices columns:", cols)
