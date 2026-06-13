from sqlalchemy.orm import Session
from sqlalchemy import text


def get_all_teams(db: Session, region: str | None = None) -> list:
    query = "SELECT * FROM rescue_teams"
    params = {}
    if region:
        query += " WHERE current_region = :region"
        params["region"] = region
    query += " ORDER BY team_id"

    teams = db.execute(text(query), params).fetchall()
    result = []
    for team in teams:
        row = dict(team._mapping)
        tid = row["team_id"]
        members = db.execute(
            text("SELECT * FROM rescuers WHERE team_id = :tid ORDER BY rescuer_id"),
            {"tid": tid},
        ).fetchall()
        victims = db.execute(
            text(
                "SELECT victim_id FROM team_victim_assignments "
                "WHERE team_id = :tid ORDER BY victim_id"
            ),
            {"tid": tid},
        ).fetchall()
        uavs = db.execute(
            text("SELECT uav_id FROM team_uav_assignments WHERE team_id = :tid"),
            {"tid": tid},
        ).fetchall()
        row["members"] = [dict(m._mapping) for m in members]
        row["assigned_victims"] = [v[0] for v in victims]
        row["assigned_users"] = row["assigned_victims"]
        row["assigned_uavs"] = [u[0] for u in uavs]
        row["member_count"] = len(row["members"])
        row["personnel_count"] = row["member_count"]
        row["assigned_victim_count"] = len(row["assigned_victims"])
        result.append(row)
    return result


def get_team(db: Session, team_id: str) -> dict | None:
    team = db.execute(
        text("SELECT * FROM rescue_teams WHERE team_id = :tid"),
        {"tid": team_id},
    ).fetchone()
    if not team:
        return None
    row = dict(team._mapping)
    members = db.execute(
        text("SELECT * FROM rescuers WHERE team_id = :tid ORDER BY rescuer_id"),
        {"tid": team_id},
    ).fetchall()
    victims = db.execute(
        text(
            "SELECT victim_id FROM team_victim_assignments "
            "WHERE team_id = :tid ORDER BY victim_id"
        ),
        {"tid": team_id},
    ).fetchall()
    uavs = db.execute(
        text("SELECT uav_id FROM team_uav_assignments WHERE team_id = :tid"),
        {"tid": team_id},
    ).fetchall()
    row["members"] = [dict(m._mapping) for m in members]
    row["assigned_victims"] = [v[0] for v in victims]
    row["assigned_users"] = row["assigned_victims"]
    row["assigned_uavs"] = [u[0] for u in uavs]
    row["personnel_count"] = len(row["members"])
    return row


def get_rescuer(db: Session, rescuer_id: str) -> dict | None:
    row = db.execute(
        text("SELECT * FROM rescuers WHERE rescuer_id = :rid"),
        {"rid": rescuer_id},
    ).fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    team = db.execute(
        text("SELECT * FROM rescue_teams WHERE team_id = :tid"),
        {"tid": data["team_id"]},
    ).fetchone()
    data["team"] = dict(team._mapping) if team else None
    return data


def count_teams_near_region(db: Session, region: str) -> int:
    if not region:
        return 0
    return db.execute(
        text(
            "SELECT COUNT(*) FROM rescue_teams "
            "WHERE current_region = :r AND status IN ('Active', 'Standby', 'deployed', 'standby', 'available')"
        ),
        {"r": region},
    ).scalar() or 0
