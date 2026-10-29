from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Contact
from app.schemas import TrackerJobRequest, TrackerVerifyRequest
from app.services.device_tracker_service import tracker_socket_client

router = APIRouter(prefix="/tracker", tags=["tracker"])


@router.get("/service-status")
def get_service_status():
    return tracker_socket_client.service_status()


@router.post("/verify")
async def verify_contact(payload: TrackerVerifyRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    result = await tracker_socket_client.verify_phone(payload.phone_number, payload.platform)
    if not result.get("verified"):
        return {"verified": False, "message": result.get("message", "Verification failed"), "platform": payload.platform}

    return {
        "verified": True,
        "jid": result.get("jid"),
        "number": payload.phone_number,
        "platform": payload.platform,
    }


@router.post("/jobs/start")
async def start_tracking_job(payload: TrackerJobRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == payload.contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    verification = await tracker_socket_client.verify_phone(payload.phone_number, payload.platform)
    if not verification.get("verified"):
        raise HTTPException(status_code=400, detail=verification.get("message", "Phone verification failed"))

    job = await tracker_socket_client.start_job(payload.contact_id, payload.phone_number, payload.platform)
    contact.status = job.state if job.state != "unknown" else "tracking"
    contact.last_seen_at = job.last_seen_at
    db.commit()

    return {
        "status": "ok",
        "job": {
            "contact_id": job.contact_id,
            "phone_number": job.phone_number,
            "platform": job.platform,
            "status": job.status,
            "state": job.state,
            "jid": job.jid,
        },
    }


@router.post("/jobs/stop")
async def stop_tracking_job(payload: TrackerJobRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == payload.contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    job = await tracker_socket_client.stop_job(payload.contact_id)
    if job is None:
        return {"status": "not_found", "contact_id": payload.contact_id}

    contact.status = "offline"
    db.commit()
    return {"status": "stopped", "job": {"contact_id": job.contact_id, "phone_number": job.phone_number, "platform": job.platform, "jid": job.jid}}


@router.get("/jobs")
def list_tracking_jobs(db: Session = Depends(get_db), user=Depends(get_current_user)):
    jobs = tracker_socket_client.list_jobs()
    contacts = {contact.id: contact for contact in db.query(Contact).all()}
    rows = []
    for contact_id, item in jobs.items():
        contact = contacts.get(contact_id)
        rows.append({
            "contact_id": contact_id,
            "phone_number": contact.phone_number if contact else item["phone_number"],
            "name": contact.name if contact else None,
            "platform": item["platform"],
            "status": item["status"],
            "state": item["state"],
            "jid": item.get("jid"),
            "rtt_ms": item.get("rtt_ms"),
            "median_ms": item.get("median_ms"),
            "threshold_ms": item.get("threshold_ms"),
            "confidence": item.get("confidence"),
            "last_seen_at": item.get("last_seen_at"),
        })
    return rows


@router.get("/contacts")
def list_tracker_status(db: Session = Depends(get_db), user=Depends(get_current_user)):
    contacts = db.query(Contact).all()
    jobs = tracker_socket_client.list_jobs()
    rows = []
    for contact in contacts:
        job = jobs.get(contact.id)
        state = job["state"] if job else contact.status or "unknown"
        rows.append({
            "contact_id": contact.id,
            "phone_number": contact.phone_number,
            "name": contact.name,
            "status": state,
            "rtt_ms": job["rtt_ms"] if job else None,
            "median_ms": job["median_ms"] if job else 0,
            "threshold_ms": job["threshold_ms"] if job else 0,
            "confidence": job["confidence"] if job else 0,
            "last_seen_at": job["last_seen_at"] if job else (contact.last_seen_at.isoformat() if contact.last_seen_at else None),
            "jid": job.get("jid") if job else None,
        })
    return rows
