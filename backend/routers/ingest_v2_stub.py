"""
Temporary stub endpoint for testing WBAN simulator output. Accepts coordinator
packets and logs them without any processing or database writes. Replace with the
real ingest_v2.py in migration phase M3.
"""

from fastapi import APIRouter
from fastapi import Request

router = APIRouter()


@router.post("/api/v2/ingest-stub")
async def ingest_stub(request: Request):
    body = await request.json()

    victim_id             = body.get("victim_id", "UNKNOWN")
    completeness          = body.get("packet_completeness", 0.0)
    sensor_count_received = body.get("sensor_count_received", 0)
    sensor_count_expected = body.get("sensor_count_expected", 0)

    print(
        f"[STUB] Packet received: victim={victim_id} "
        f"completeness={completeness:.2f} "
        f"sensors={sensor_count_received}/{sensor_count_expected}"
    )

    return {
        "status": "received",
        "victim_id": victim_id,
        "packet_completeness": completeness,
    }
