from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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
