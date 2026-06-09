"""
Real WBAN ingest endpoint for coordinator packets. This replaces the stub endpoint
from phase M2. Each POST creates one coordinator_packets row and one
telemetry_readings row per sensor. The AI pipeline and imputation pipeline are not
yet called here — they are added in phases M4 and M5.
"""

import datetime
import json, time, os

# #region agent log - debug e91cd1
_DBG_LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'debug-e91cd1.log')
def _dbg(msg, data, hyp):
    entry = {"sessionId":"e91cd1","timestamp":int(time.time()*1000),"location":"routers/ingest_v2.py","message":msg,"data":data,"hypothesisId":hyp}
    open(_DBG_LOG,'a').write(json.dumps(entry)+'\n')
# #endregion

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.coordinator_packet import CoordinatorPacketIn, CoordinatorPacketOut
from services.telemetry_service_v2 import (
    check_duplicate_packet,
    insert_coordinator_packet,
    insert_telemetry_readings,
    upsert_victim_status,
    update_readings_with_ai_results,
)
from services.alert_service import create_alert
from ai import run_ai_pipeline
from services.victim_service import victim_exists, get_victim_profile_for_pipeline
from services.preprocessing.imputation_service import impute_missing_readings, update_recent_readings_cache
from services.preprocessing.confidence_scorer import assign_confidence_scores, compute_packet_confidence
from services.preprocessing.packet_validator import validate_reading_ranges

router = APIRouter()


@router.post("/api/v2/ingest", response_model=CoordinatorPacketOut)
async def ingest_coordinator_packet(
    packet: CoordinatorPacketIn,
    db: Session = Depends(get_db),
):
    # #region agent log - debug e91cd1
    _dbg("handler_entered", {"victim_id": packet.victim_id}, "H-B")
    # #endregion

    # STEP 1 — Check victim exists
    # #region agent log - debug e91cd1
    try:
        _exists = victim_exists(db, packet.victim_id)
        _dbg("victim_exists_result", {"victim_id": packet.victim_id, "exists": _exists}, "H-A")
    except Exception as _e:
        _dbg("victim_exists_exception", {"error": str(_e), "type": type(_e).__name__}, "H-C")
        raise
    # #endregion
    if not _exists:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unknown victim_id: {packet.victim_id}. "
                "Victim must be seeded before ingesting packets."
            ),
        )
    # #region agent log - debug e91cd1
    _dbg("past_victim_check", {"victim_id": packet.victim_id}, "H-A")
    # #endregion

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

    # STEP 6b — Load victim profile
    victim_profile = get_victim_profile_for_pipeline(db, packet.victim_id)

    # STEP 6c — Build flat readings dict for AI (use imputed values where raw is missing)
    flat_readings = {}
    for sensor_id, reading_data in enriched_readings.items():
        if reading_data["raw_value"] is not None:
            flat_readings[sensor_id] = reading_data["raw_value"]
        elif reading_data["imputed_value"] is not None:
            flat_readings[sensor_id] = reading_data["imputed_value"]

    # STEP 6d — Run AI pipeline
    ai_result = run_ai_pipeline(packet.victim_id, flat_readings, victim_profile, sos_active=False)

    # STEP 6e — Update anomaly flags in database
    update_readings_with_ai_results(db, packet_id, ai_result)

    # STEP 6f — Create any generated alerts
    for alert_dict in ai_result.get("alerts", []):
        alert_dict["packet_id"] = packet_id
        create_alert(db, alert_dict)

    # STEP 7 — Print success log
    print(
        f"[INGEST] victim={packet.victim_id} packet_id={packet_id} "
        f"completeness={packet.packet_completeness:.2f} "
        f"score={ai_result['severity_score']} priority={ai_result['priority_class']} "
        f"alerts={len(ai_result['alerts'])}"
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
