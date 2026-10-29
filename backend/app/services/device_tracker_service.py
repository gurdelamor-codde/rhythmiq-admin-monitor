import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, Optional

import socketio

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TrackerJob:
    id: str
    contact_id: str
    phone_number: str
    platform: str
    status: str = "pending"
    state: str = "unknown"
    jid: Optional[str] = None
    rtt_ms: Optional[float] = None
    median_ms: float = 0.0
    threshold_ms: float = 0.0
    confidence: float = 0.0
    last_seen_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TrackerSocketClient:
    def __init__(self):
        self._lock = Lock()
        self._jobs: Dict[str, TrackerJob] = {}
        self._jid_to_job: Dict[str, str] = {}
        self._verification_futures: Dict[str, asyncio.Future] = {}
        self._sio = socketio.AsyncClient(reconnection=True, logger=False, engineio_logger=False)
        self._connected = False

        @self._sio.event
        async def connect():
            self._connected = True
            logger.info("Connected to external tracker service at %s", settings.tracker_service_url)

        @self._sio.event
        async def disconnect():
            self._connected = False
            logger.info("Disconnected from external tracker service")

        @self._sio.event
        async def connect_error(data):
            logger.warning("Tracker service connection error: %s", data)
            self._connected = False

        @self._sio.on("contact-added")
        async def _handle_contact_added(data):
            payload = data or {}
            phone = payload.get("number")
            jid = payload.get("jid")
            if phone:
                fut = self._verification_futures.pop(str(phone), None)
                if fut and not fut.done():
                    fut.set_result({"verified": True, "jid": jid, "number": phone, "platform": payload.get("platform", "whatsapp")})

        @self._sio.on("error")
        async def _handle_error(data):
            payload = data or {}
            key = payload.get("number") or payload.get("jid")
            if key:
                fut = self._verification_futures.pop(str(key), None)
                if fut and not fut.done():
                    fut.set_result({"verified": False, "message": payload.get("message", "Tracking failed")})

        @self._sio.on("tracker-update")
        async def _handle_tracker_update(data):
            payload = data or {}
            jid = payload.get("jid")
            if not jid:
                return

            with self._lock:
                job_id = self._jid_to_job.get(jid)
                job = self._jobs.get(job_id) if job_id else None
                if not job:
                    return

                devices = payload.get("devices") or []
                if devices:
                    device = devices[0]
                    state = str(device.get("state", "unknown")).lower()
                    job.state = state
                    job.status = "tracking" if state in {"online", "standby", "offline"} else "pending"
                    job.rtt_ms = device.get("rtt")
                    job.confidence = 1.0 if state == "online" else 0.7 if state == "standby" else 0.2
                    job.last_seen_at = datetime.now(timezone.utc)

                if payload.get("median") is not None:
                    job.median_ms = float(payload.get("median") or 0)
                if payload.get("threshold") is not None:
                    job.threshold_ms = float(payload.get("threshold") or 0)

    async def start(self):
        if not self.enabled() or self._connected:
            return
        try:
            await self._sio.connect(settings.tracker_service_url)
            self._connected = True
        except Exception as exc:  # pragma: no cover
            logger.warning("Could not connect to external tracker service: %s", exc)
            self._connected = False

    async def stop(self):
        if self._connected:
            await self._sio.disconnect()
        self._connected = False

    def enabled(self) -> bool:
        return bool(settings.tracker_service_enabled)

    def connected(self) -> bool:
        return self._connected

    async def verify_phone(self, phone_number: str, platform: str = "whatsapp") -> Dict[str, Any]:
        if not self.enabled():
            return {"verified": False, "message": "External tracker service is disabled."}

        await self.start()
        if not self._connected:
            return {"verified": False, "message": "External tracker service is unavailable."}

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        key = str(phone_number).strip()
        self._verification_futures[key] = fut
        try:
            await self._sio.emit("add-contact", {"number": phone_number, "platform": platform})
            return await asyncio.wait_for(fut, timeout=settings.tracker_service_timeout_seconds)
        except asyncio.TimeoutError:
            return {"verified": False, "message": "Phone verification timed out."}

    async def start_job(self, contact_id: str, phone_number: str, platform: str = "whatsapp") -> TrackerJob:
        phone = str(phone_number).strip()
        with self._lock:
            job = TrackerJob(
                id=f"job-{contact_id}",
                contact_id=contact_id,
                phone_number=phone,
                platform=platform,
                status="starting",
                state="unknown",
            )
            self._jobs[job.id] = job

        result = await self.verify_phone(phone, platform)
        if not result.get("verified"):
            with self._lock:
                job.status = "failed"
                job.state = "unknown"
            return job

        jid = str(result.get("jid") or phone)
        with self._lock:
            job.jid = jid
            job.status = "tracking"
            job.state = "online"
            job.last_seen_at = datetime.now(timezone.utc)
            self._jid_to_job[jid] = job.id

        return job

    async def stop_job(self, contact_id: str) -> Optional[TrackerJob]:
        with self._lock:
            job = next((j for j in self._jobs.values() if j.contact_id == contact_id), None)
            if job is None:
                return None

        target_jid = job.jid or job.phone_number
        if self._connected:
            try:
                await self._sio.emit("remove-contact", target_jid)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not stop tracker for contact %s: %s", contact_id, exc)

        with self._lock:
            job.status = "stopped"
            job.state = "offline"
            self._jobs.pop(job.id, None)
            for jid, job_id in list(self._jid_to_job.items()):
                if job_id == job.id:
                    self._jid_to_job.pop(jid, None)
        return job

    def service_status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled(),
            "connected": self._connected,
            "url": settings.tracker_service_url,
            "jobs": len(self._jobs),
        }

    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            payload = {}
            for job in self._jobs.values():
                payload[job.contact_id] = {
                    "contact_id": job.contact_id,
                    "phone_number": job.phone_number,
                    "platform": job.platform,
                    "status": job.status,
                    "state": job.state,
                    "jid": job.jid,
                    "rtt_ms": job.rtt_ms,
                    "median_ms": job.median_ms,
                    "threshold_ms": job.threshold_ms,
                    "confidence": job.confidence,
                    "last_seen_at": job.last_seen_at.isoformat() if job.last_seen_at else None,
                }
            return payload

    def status_for_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = next((j for j in self._jobs.values() if j.contact_id == contact_id), None)
            if job is None:
                return None
            return {
                "contact_id": job.contact_id,
                "phone_number": job.phone_number,
                "platform": job.platform,
                "status": job.status,
                "state": job.state,
                "jid": job.jid,
                "rtt_ms": job.rtt_ms,
                "median_ms": job.median_ms,
                "threshold_ms": job.threshold_ms,
                "confidence": job.confidence,
                "last_seen_at": job.last_seen_at.isoformat() if job.last_seen_at else None,
            }


tracker_socket_client = TrackerSocketClient()

__all__ = ["TrackerJob", "TrackerSocketClient", "tracker_socket_client"]
