from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: Optional[str] = "member"
    timezone: Optional[str] = "UTC"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ContactCreate(BaseModel):
    phone_number: str
    name: Optional[str] = None
    team_id: Optional[str] = None
    status: Optional[str] = "unknown"


class ContactRead(BaseModel):
    id: str
    team_id: Optional[str]
    phone_number: str
    name: Optional[str]
    status: Optional[str]
    last_seen_at: Optional[datetime]
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventCreate(BaseModel):
    contact_id: str
    event_type: str
    event_subtype: Optional[str] = None
    direction: Optional[str] = None
    channel: str = "phone"
    event_time: datetime
    response_latency_ms: Optional[int] = None
    message_length: Optional[int] = None
    message_mode: Optional[str] = None
    task_context: Optional[str] = None
    urgency_score: Optional[float] = None
    mood_label: Optional[str] = None
    context_tags: Optional[Dict[str, Any]] = None


class TrackerMeasurement(BaseModel):
    rtt_ms: Optional[float] = None
    event_time: Optional[datetime] = None
    channel: str = "device_activity_tracker"
    message_length: Optional[int] = None


class TrackerVerifyRequest(BaseModel):
    phone_number: str
    platform: str = "whatsapp"


class TrackerJobRequest(BaseModel):
    contact_id: str
    phone_number: str
    platform: str = "whatsapp"


class TrackerStatusResponse(BaseModel):
    contact_id: str
    phone_number: str
    name: Optional[str]
    status: str
    rtt_ms: Optional[float]
    median_ms: float
    threshold_ms: float
    confidence: float
    last_seen_at: Optional[datetime]
