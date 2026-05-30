"""
Standalone script — run once to create all database tables.

    cd backend
    python init_db.py
"""

from database import Base, engine
import models  # noqa: F401 — registers all ORM classes with Base.metadata

Base.metadata.create_all(bind=engine)
print("Database tables created successfully.")
print("Tables:", list(Base.metadata.tables.keys()))
