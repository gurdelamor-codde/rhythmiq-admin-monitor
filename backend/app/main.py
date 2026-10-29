from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.db import SessionLocal, engine
from app.models import Base, User
from app.routers import auth, contacts, events, insights, leaderboard
from app.routers.tracker import router as tracker_router
from app.services.device_tracker_service import tracker_socket_client

Base.metadata.create_all(bind=engine)


def ensure_default_admin_user() -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@rhythmiq.io").first()
        if user is None:
            db.add(
                User(
                    id="admin-default",
                    email="admin@rhythmiq.io",
                    name="Admin",
                    password_hash=hash_password("admin123"),
                    role="admin",
                    timezone="UTC",
                )
            )
            db.commit()
    finally:
        db.close()


app = FastAPI(title="RhythmIQ Admin Monitor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    ensure_default_admin_user()
    if tracker_socket_client.enabled():
        await tracker_socket_client.start()


app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(events.router)
app.include_router(insights.router)
app.include_router(leaderboard.router)
app.include_router(tracker_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "tracker_service_enabled": tracker_socket_client.enabled(),
        "tracker_service_connected": tracker_socket_client.connected(),
    }
