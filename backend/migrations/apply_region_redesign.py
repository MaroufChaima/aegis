"""
Phase R0 schema foundation for the AEGIS region redesign.
Safe to run multiple times (idempotent checks).

Run from backend/: python migrations/apply_region_redesign.py
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
        # victim_current_state — altitude, emergency tracking, UAV backups, region
        for col, typ in [
            ("altitude_m", "REAL"),
            ("emergency_status", "TEXT DEFAULT 'normal'"),
            ("uav_backup_ids", "TEXT DEFAULT '[]'"),
            ("current_region", "TEXT"),
        ]:
            if not _column_exists(conn, "victim_current_state", col.split()[0]):
                conn.execute(text(f"ALTER TABLE victim_current_state ADD COLUMN {col}"))
                print(f"Added victim_current_state.{col.split()[0]}")

        # uav_positions — home region (status default handled in ORM / seeds)
        if not _column_exists(conn, "uav_positions", "home_region"):
            conn.execute(text("ALTER TABLE uav_positions ADD COLUMN home_region TEXT"))
            print("Added uav_positions.home_region")

        # rescue_teams — organization type
        if not _column_exists(conn, "rescue_teams", "team_type"):
            conn.execute(text("ALTER TABLE rescue_teams ADD COLUMN team_type TEXT"))
            print("Added rescue_teams.team_type")

        if not _table_exists(conn, "emergency_events"):
            conn.execute(text("""
                CREATE TABLE emergency_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    region TEXT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    severity TEXT,
                    notes TEXT
                )
            """))
            print("Created emergency_events")

        if not _table_exists(conn, "team_uav_assignments"):
            conn.execute(text("""
                CREATE TABLE team_uav_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_id TEXT NOT NULL,
                    uav_id TEXT NOT NULL,
                    assigned_at TEXT,
                    FOREIGN KEY (team_id) REFERENCES rescue_teams(team_id)
                )
            """))
            print("Created team_uav_assignments")

        conn.commit()
    print("Phase R0 schema migration complete.")


if __name__ == "__main__":
    main()
