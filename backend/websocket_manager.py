"""
WebSocket connection manager for the AEGIS backend.

Maintains the pool of active browser connections and broadcasts
JSON messages to all of them. Dead connections are silently
removed so a single dropped client never blocks other recipients.
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import WebSocket

log = logging.getLogger(__name__)


class ConnectionManager:
    """Manages a pool of active WebSocket connections.

    Responsibilities:
    - Track every connected React client.
    - Broadcast a JSON-serialisable dict to all active connections.
    - Remove connections that have closed or errored without raising.

    Thread / concurrency notes:
        FastAPI runs WebSocket handlers in an async context. All methods
        here are async-safe for single-process uvicorn. A multi-worker
        deployment would require a pub/sub backend (e.g. Redis) — deferred
        to Phase 5+.
    """

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept the handshake and register the connection.

        Must be called before any send/receive operations on the socket.

        Args:
            websocket: Incoming WebSocket from the FastAPI route handler.
        """
        await websocket.accept()
        self._connections.append(websocket)
        log.info("WebSocket connected  (total=%d)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a connection from the pool.

        Safe to call even if the socket is not currently registered
        (e.g. duplicate disconnect). Does not close the socket — the
        caller's exception handler is responsible for that.

        Args:
            websocket: The WebSocket to deregister.
        """
        self._connections = [ws for ws in self._connections if ws is not websocket]
        log.info("WebSocket disconnected (total=%d)", len(self._connections))

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to every active connection.

        Iterates a snapshot of the current pool. If sending to any
        connection fails (closed tab, network drop), that connection is
        silently removed and iteration continues — one dead client must
        never prevent others from receiving updates.

        Args:
            message: JSON-serialisable dict. Must conform to the envelope
                     defined in API_FLOW.md::

                         {
                           "type":      "<message_type>",
                           "timestamp": "<ISO-8601>",
                           "payload":   { ... }
                         }
        """
        if not self._connections:
            return

        text = json.dumps(message, default=str)
        dead: list[WebSocket] = []

        for ws in list(self._connections):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)
            log.debug("Removed dead WebSocket connection")


def _make_envelope(msg_type: str, payload: dict) -> dict:
    """Wrap a payload in the standard API_FLOW.md message envelope.

    Args:
        msg_type: One of "telemetry_update", "alert", "uav_update",
                  "device_status_change".
        payload:  The inner payload dict specific to the message type.

    Returns:
        Dict ready to pass to ``manager.broadcast()``.
    """
    return {
        "type":      msg_type,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload":   payload,
    }


def make_telemetry_update(data: dict, ai_result: dict) -> dict:
    """Build a ``telemetry_update`` envelope from ingest data and AI results.

    Combines the raw telemetry fields with AI scores into the payload shape
    documented in API_FLOW.md.

    Args:
        data:      Preprocessed telemetry dict from the ingest pipeline.
        ai_result: Dict returned by ``run_ai_pipeline()``.

    Returns:
        Complete message envelope ready for broadcast.
    """
    payload = {
        "device_id":     data["device_id"],
        "latitude":      data.get("latitude"),
        "longitude":     data.get("longitude"),
        "heart_rate":    data.get("heart_rate"),
        "temperature":   data.get("temperature"),
        "sos_signal":    bool(data.get("sos_signal", False)),
        "movement":      bool(data.get("movement", True)),
        "rssi":          data.get("rssi"),
        "battery":       data.get("battery"),
        "uav_relay_id":  data.get("uav_relay_id"),
        "last_seen":     data.get("timestamp"),
        "status":        "sos" if data.get("sos_signal") else "online",
        "severity_score": ai_result["severity_score"],
        "priority_class": ai_result["priority_class"],
        "is_anomaly":     ai_result["is_anomaly"],
        "anomaly_score":  ai_result["anomaly_score"],
    }
    return _make_envelope("telemetry_update", payload)


def make_alert_message(alert_record) -> dict:
    """Build an ``alert`` envelope from a persisted Alert ORM instance.

    Args:
        alert_record: Alert ORM object returned by ``create_alert()``.

    Returns:
        Complete message envelope ready for broadcast.
    """
    payload = {
        "id":           alert_record.id,
        "device_id":    alert_record.device_id,
        "alert_type":   alert_record.alert_type,
        "severity":     alert_record.severity,
        "message":      alert_record.message,
        "ai_confidence": alert_record.ai_confidence,
        "acknowledged": False,
    }
    return _make_envelope("alert", payload)


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------

manager = ConnectionManager()
"""Shared ConnectionManager instance.

Import this singleton so all ingest requests share the same connection pool.
Creating a new instance per request would produce an empty pool on every call.

Usage::

    from websocket_manager import manager
    await manager.broadcast(message)
"""
