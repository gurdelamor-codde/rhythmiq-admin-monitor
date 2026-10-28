from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median
from threading import Lock
from typing import Dict, List, Optional


@dataclass
class TrackerSnapshot:
    contact_id: str
    state: str
    rtt_ms: Optional[float]
    median_ms: float
    threshold_ms: float
    moving_avg_ms: float
    confidence: float
    last_seen_at: datetime


class DeviceActivityEngine:
    def __init__(self):
        self._history: Dict[str, List[float]] = {}
        self._snapshots: Dict[str, TrackerSnapshot] = {}
        self._lock = Lock()

    def ingest(self, contact_id: str, rtt_ms: Optional[float], observed_at: Optional[datetime] = None) -> TrackerSnapshot:
        observed_at = observed_at or datetime.now(timezone.utc)

        with self._lock:
            history = self._history.setdefault(contact_id, [])

            if rtt_ms is not None:
                history.append(float(rtt_ms))

            history = history[-200:]
            self._history[contact_id] = history

            if not history:
                snapshot = TrackerSnapshot(
                    contact_id=contact_id,
                    state="offline",
                    rtt_ms=None,
                    median_ms=0.0,
                    threshold_ms=0.0,
                    moving_avg_ms=0.0,
                    confidence=0.0,
                    last_seen_at=observed_at,
                )
                self._snapshots[contact_id] = snapshot
                return snapshot

            median_ms = median(history)
            threshold_ms = max(200.0, median_ms * 0.9)
            recent = history[-3:]
            moving_avg_ms = sum(recent) / len(recent)

            if rtt_ms is None:
                state = "offline"
                confidence = 0.0
            elif rtt_ms < threshold_ms:
                state = "online"
                confidence = min(1.0, max(0.2, 1.0 - (abs(rtt_ms - threshold_ms) / max(threshold_ms, 1.0))))
            else:
                state = "standby"
                confidence = min(1.0, max(0.2, 1.0 - (abs(rtt_ms - threshold_ms) / (threshold_ms * 2.5))))

            snapshot = TrackerSnapshot(
                contact_id=contact_id,
                state=state,
                rtt_ms=float(rtt_ms) if rtt_ms is not None else None,
                median_ms=float(median_ms),
                threshold_ms=float(threshold_ms),
                moving_avg_ms=float(moving_avg_ms),
                confidence=float(confidence),
                last_seen_at=observed_at,
            )
            self._snapshots[contact_id] = snapshot
            return snapshot

    def status_for(self, contact_id: str) -> Optional[TrackerSnapshot]:
        return self._snapshots.get(contact_id)

    def list_for_contact_ids(self, contact_ids: List[str]) -> Dict[str, TrackerSnapshot]:
        result: Dict[str, TrackerSnapshot] = {}
        for contact_id in contact_ids:
            snapshot = self.status_for(contact_id)
            if snapshot:
                result[contact_id] = snapshot
        return result


device_activity_engine = DeviceActivityEngine()
