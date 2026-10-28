from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Contact, ContactEvent
from app.schemas import EventCreate

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/")
def create_event(payload: EventCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == payload.contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    event = ContactEvent(
        id=str(__import__("uuid").uuid4()),
        user_id=user.id,
        contact_id=payload.contact_id,
        team_id=contact.team_id,
        event_type=payload.event_type,
        event_subtype=payload.event_subtype,
        direction=payload.direction,
        channel=payload.channel,
        event_time=payload.event_time,
        response_latency_ms=payload.response_latency_ms,
        message_length=payload.message_length,
        message_mode=payload.message_mode,
        task_context=payload.task_context,
        urgency_score=payload.urgency_score,
        mood_label=payload.mood_label,
        context_tags=payload.context_tags,
    )

    contact.last_seen_at = payload.event_time
    contact.status = payload.event_type

    db.add(event)
    db.commit()
    return {"message": "Event recorded"}

@router.get("/")
def list_events(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(ContactEvent).filter(ContactEvent.user_id == user.id).all()
