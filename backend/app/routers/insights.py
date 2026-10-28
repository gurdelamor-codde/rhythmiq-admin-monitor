from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import ContactEvent
from app.services.features import compute_feature_snapshot
from app.services.inference import infer_state

router = APIRouter(prefix="/insights", tags=["insights"])

@router.get("/")
def get_insights(db: Session = Depends(get_db), user=Depends(get_current_user)):
    features = compute_feature_snapshot(db, user.id)
    event_count = db.query(ContactEvent).filter(ContactEvent.user_id == user.id).count()
    state = infer_state(features)

    explanation = (
        f"Recent phone communication suggests a {state.lower()} state. "
        f"Latency is {features['median_response_latency_ms']:.0f} ms, "
        f"burst activity is {features['message_burst_count']:.0f}, and "
        f"offline gap is {features['offline_gap_minutes']:.0f} minutes."
    )

    return {
        "state": state,
        "event_count": event_count,
        "features": features,
        "explanation": explanation,
    }
