"""
Database initialization script for AEGIS. Run this once before starting the backend:
python init_db.py. This script is safe to run multiple times — it uses create_all
which skips tables that already exist. It will NOT delete existing data.
"""

from database import engine, Base
import models


def init_db():
    print("Initializing AEGIS database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized. Tables created or verified:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
    print('Tables include new WBAN current-state table: victim_current_state')


if __name__ == "__main__":
    init_db()
