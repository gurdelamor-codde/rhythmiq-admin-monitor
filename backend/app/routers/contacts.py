from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Contact, Team
from app.schemas import ContactCreate, ContactRead

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.post("/", response_model=ContactRead)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can add contacts")

    if db.query(Contact).filter(Contact.phone_number == payload.phone_number).first():
        raise HTTPException(status_code=400, detail="Phone number already exists")

    team = db.query(Team).first()
    if not team:
        team = Team(
            id=str(__import__("uuid").uuid4()),
            name="My Team",
        )
        db.add(team)
        db.commit()
        db.refresh(team)

    contact = Contact(
        id=str(__import__("uuid").uuid4()),
        team_id=team.id,
        phone_number=payload.phone_number,
        name=payload.name,
        status=payload.status,
        active=True,
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact

@router.get("/", response_model=list[ContactRead])
def list_contacts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view contacts")
    return db.query(Contact).all()
