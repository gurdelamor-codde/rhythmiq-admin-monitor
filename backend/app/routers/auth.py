from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.config import settings
from app.deps import get_db
from app.models import User
from app.schemas import TokenResponse, UserCreate

router = APIRouter(tags=["auth"])

@router.post("/users/", response_model=dict)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        id=str(__import__("uuid").uuid4()),
        email=str(payload.email),
        name=payload.name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        timezone=payload.timezone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created"}

@router.post("/auth/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return {"access_token": access_token, "token_type": "bearer"}
