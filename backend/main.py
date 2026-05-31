from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.ingest import router as ingest_router
from routers.victims import router as victims_router

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


app.include_router(ingest_router)
app.include_router(victims_router)
