from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine
from app.models import Base
from app.routers import auth, contacts, events, insights, leaderboard

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RhythmIQ Admin Monitor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(events.router)
app.include_router(insights.router)
app.include_router(leaderboard.router)

@app.get("/health")
def health():
    return {"status": "ok"}
