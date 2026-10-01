import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import meetings

app = FastAPI(title="Spry API")

origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router)


@app.get("/health")
def health():
    return {"status": "ok"}
