"""
Database operations for the uav_positions table.
Rows are upserted on every simulator tick — each UAV always has exactly
one current-state row identified by uav_id.
"""

from sqlalchemy.orm import Session

from models.uav import UAVPosition


def upsert_uav(db: Session, data: dict) -> UAVPosition:
    """Create or update the UAV position row for one UAV.

    Uses uav_id as the unique key. On first tick from a new UAV, inserts
    a row. On subsequent ticks, updates all position and status fields.

    Args:
        db:   SQLAlchemy session.
        data: Dict matching the UAVUpdateIn schema.

    Returns:
        The UAVPosition ORM instance after commit.
    """
    uav = db.query(UAVPosition).filter(UAVPosition.uav_id == data["uav_id"]).first()

    if uav is None:
        uav = UAVPosition(uav_id=data["uav_id"])
        db.add(uav)

    uav.timestamp         = data["timestamp"]
    uav.latitude          = data["latitude"]
    uav.longitude         = data["longitude"]
    uav.altitude          = data["altitude"]
    uav.battery           = data["battery"]
    uav.status            = data["status"]
    uav.coverage_radius   = data["coverage_radius"]
    uav.connected_devices = data["connected_devices"]

    db.commit()
    db.refresh(uav)
    return uav


def get_all_uavs(db: Session) -> list[UAVPosition]:
    """Return all UAV position rows ordered by uav_id.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of UAVPosition ORM instances.
    """
    return db.query(UAVPosition).order_by(UAVPosition.uav_id).all()
