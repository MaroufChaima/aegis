"""
Real WBAN ingest endpoint for coordinator packets. This replaces the stub endpoint
from phase M2. Each POST creates one coordinator_packets row and one
telemetry_readings row per sensor. The AI pipeline and imputation pipeline are not
yet called here — they are added in phases M4 and M5.
"""

import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.coordinator_packet import CoordinatorPacketIn, CoordinatorPacketOut
from services.telemetry_service_v2 import (
    check_duplicate_packet,
    insert_coordinator_packet,
    insert_telemetry_readings,
    upsert_victim_status,
)
from services.victim_service import victim_exists
from services.preprocessing.imputation_service import impute_missing_readings, update_recent_readings_cache
from services.preprocessing.confidence_scorer import assign_confidence_scores, compute_packet_confidence
from services.preprocessing.packet_validator import validate_reading_ranges

router = APIRouter()


@router.post("/api/v2/ingest", response_model=CoordinatorPacketOut)
async def ingest_coordinator_packet(
    packet: CoordinatorPacketIn,
    db: Session = Depends(get_db),
):
    # STEP 1 — Check victim exists
    if not victim_exists(db, packet.victim_id):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unknown victim_id: {packet.victim_id}. "
                "Victim must be seeded before ingesting packets."
            ),
        )

    # STEP 2 — Check for duplicate
    if check_duplicate_packet(db, packet.victim_id, packet.timestamp):
        print(
            f"[DUPLICATE] Skipping duplicate packet: "
            f"victim={packet.victim_id} timestamp={packet.timestamp}"
        )
        return CoordinatorPacketOut(
            status="duplicate",
            victim_id=packet.victim_id,
            packet_id=None,
            packet_completeness=packet.packet_completeness,
            readings_stored=0,
            message="Duplicate packet skipped",
        )

    # STEP 3 — Build packet dict for insertion
    packet_data = {
        "victim_id":             packet.victim_id,
        "coordinator_id":        packet.coordinator_id,
        "uav_relay_id":          packet.uav_relay_id,
        "timestamp":             packet.timestamp,
        "received_at":           datetime.datetime.utcnow().isoformat(),
        "sensor_count_expected": packet.sensor_count_expected,
        "sensor_count_received": packet.sensor_count_received,
        "packet_completeness":   packet.packet_completeness,
        "rssi":                  packet.rssi,
        "snr":                   packet.snr,
        "packet_quality":        packet.packet_quality,
    }

    # STEP 4 — Insert coordinator packet
    try:
        packet_id = insert_coordinator_packet(db, packet_data)
    except Exception as e:
        print(f"[ERROR] Failed to insert coordinator packet: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to store coordinator packet",
        )

    # STEP 5a — Run imputation
    enriched_readings = impute_missing_readings(
        db, packet.victim_id, packet.readings, packet.sensor_statuses or {}, packet.timestamp
    )

    # STEP 5b — Assign confidence scores
    enriched_readings = assign_confidence_scores(
        enriched_readings, packet.sensor_statuses or {}, packet.timestamp
    )

    # STEP 5c — Insert readings with imputation data
    readings_stored = insert_telemetry_readings(
        db, packet_id, packet.victim_id, packet.timestamp, enriched_readings
    )

    # STEP 5d — Update the KNN cache
    update_recent_readings_cache(packet.victim_id, packet.readings, packet.timestamp)

    # STEP 6 — Update victim status
    upsert_victim_status(
        db,
        packet.victim_id,
        packet.uav_relay_id or "UAV-UNKNOWN",
        packet.timestamp,
    )

    # STEP 7 — Print success log
    print(
        f"[INGEST] victim={packet.victim_id} packet_id={packet_id} "
        f"completeness={packet.packet_completeness:.2f} readings={readings_stored}"
    )

    # STEP 8 — Return response
    return CoordinatorPacketOut(
        status="ok",
        victim_id=packet.victim_id,
        packet_id=packet_id,
        packet_completeness=packet.packet_completeness,
        readings_stored=readings_stored,
        message=None,
    )
