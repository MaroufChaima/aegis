from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from routers.ingest import router as ingest_router
from routers.victims import router as victims_router
from routers.uavs import router as uavs_router
from routers.simulation import router as simulation_router
from routers.analytics import router as analytics_router
from websocket_manager import manager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Accept and maintain a WebSocket connection from a React client.

    Registers the connection in the shared pool, then loops waiting for
    incoming frames (the client sends nothing meaningful — this is a
    push-only channel). Cleans up the connection on disconnect or error.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive; client messages are ignored.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


app.include_router(ingest_router)
app.include_router(victims_router)
app.include_router(uavs_router)
app.include_router(simulation_router)
app.include_router(analytics_router)
