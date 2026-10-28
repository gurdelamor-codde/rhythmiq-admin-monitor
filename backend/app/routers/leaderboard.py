from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import ContactEvent, User
from app.services.features import compute_feature_snapshot

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("/")
def get_leaderboard(db: Session = Depends(get_db), user=Depends(get_current_user)):
    users = db.query(User).all()
    items = []

    for u in users:
        features = compute_feature_snapshot(db, u.id)
        event_count = db.query(ContactEvent).filter(ContactEvent.user_id == u.id).count()
        score = (
            (features["median_response_latency_ms"] / 1000.0) * 0.2
            + features["message_burst_count"] * 2.0
            + features["urgency_score"] * 25.0
            + event_count * 1.2
        )
        items.append({"name": u.name, "score": round(score, 2)})

    items = sorted(items, key=lambda x: x["score"], reverse=True)
    result = []
    for idx, item in enumerate(items, start=1):
        result.append({"rank": idx, "name": item["name"], "score": item["score"]})

    return result
