from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json, time, os

# #region agent log - debug e91cd1
_DBG_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'debug-e91cd1.log')
def _dbg_main(msg, data, hyp):
    entry = {"sessionId":"e91cd1","timestamp":int(time.time()*1000),"location":"main.py","message":msg,"data":data,"hypothesisId":hyp}
    open(_DBG_LOG,'a').write(json.dumps(entry)+'\n')
# #endregion

from routers.ingest import router as ingest_router
from routers.victims import router as victims_router
from routers.uavs import router as uavs_router
from routers.simulation import router as simulation_router
from routers.analytics import router as analytics_router
from routers.profiles import router as profiles_router
from routers.ingest_v2 import router as ingest_v2_router
from websocket_manager import manager

app = FastAPI()

# #region agent log - debug e91cd1
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    _dbg_main("pydantic_validation_error", {"errors": exc.errors(), "url": str(request.url)}, "H-B")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
# #endregion

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
app.include_router(profiles_router)
app.include_router(ingest_v2_router)
