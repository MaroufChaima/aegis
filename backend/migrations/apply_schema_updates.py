"""
Apply schema updates for phases B–G. Safe to run multiple times (idempotent checks).
Run from backend/: python migrations/apply_schema_updates.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
        {"t": table},
    ).fetchone()
    return row is not None


def main():
    with engine.connect() as conn:
        # victims — anthropometrics + region
        for col, typ in [("height_cm", "REAL"), ("weight_kg", "REAL"), ("home_region", "TEXT")]:
            if not _column_exists(conn, "victims", col):
                conn.execute(text(f"ALTER TABLE victims ADD COLUMN {col} {typ}"))
                print(f"Added victims.{col}")

        # uav_positions — display name + region
        for col, typ in [("name", "TEXT"), ("current_region", "TEXT")]:
            if not _column_exists(conn, "uav_positions", col):
                conn.execute(text(f"ALTER TABLE uav_positions ADD COLUMN {col} {typ}"))
                print(f"Added uav_positions.{col}")

        if not _table_exists(conn, "rescue_teams"):
            conn.execute(text("""
                CREATE TABLE rescue_teams (
                    team_id TEXT PRIMARY KEY,
                    team_name TEXT NOT NULL,
                    specialization TEXT,
                    current_region TEXT,
                    status TEXT DEFAULT 'available',
                    latitude REAL,
                    longitude REAL
                )
            """))
            print("Created rescue_teams")

        if not _table_exists(conn, "rescuers"):
            conn.execute(text("""
                CREATE TABLE rescuers (
                    rescuer_id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    role TEXT,
                    age INTEGER,
                    phone TEXT,
                    years_experience INTEGER,
                    FOREIGN KEY (team_id) REFERENCES rescue_teams(team_id)
                )
            """))
            print("Created rescuers")

        if not _table_exists(conn, "team_victim_assignments"):
            conn.execute(text("""
                CREATE TABLE team_victim_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_id TEXT NOT NULL,
                    victim_id TEXT NOT NULL,
                    assigned_at TEXT,
                    FOREIGN KEY (team_id) REFERENCES rescue_teams(team_id)
                )
            """))
            print("Created team_victim_assignments")

        conn.commit()
    print("Schema migration complete.")


if __name__ == "__main__":
    main()
