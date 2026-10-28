from statistics import median, pstdev
from typing import Dict
from app.models import ContactEvent


def _safe_mean(values):
    return sum(values) / len(values) if values else 0.0


def compute_feature_snapshot(db, user_id: str) -> Dict[str, float]:
    events = db.query(ContactEvent).filter(ContactEvent.user_id == user_id).all()

    if not events:
        return {
            "median_response_latency_ms": 0.0,
            "response_variance": 0.0,
            "message_burst_count": 0.0,
            "voice_note_ratio": 0.0,
            "task_ack_lag_ms": 0.0,
            "hour_of_day": 0.0,
            "day_of_week": 0.0,
            "urgency_score": 0.0,
            "recovery_lag_ms": 0.0,
            "context_switches": 0.0,
            "offline_gap_minutes": 0.0,
            "presence_confidence": 0.0,
        }

    latencies = [e.response_latency_ms for e in events if e.response_latency_ms is not None]
    urgencies = [e.urgency_score for e in events if e.urgency_score is not None]
    event_hours = [e.event_time.hour for e in events]
    event_days = [e.event_time.weekday() for e in events]

    response_variance = pstdev(latencies) if len(latencies) > 1 else 0.0
    burst_count = 0

    if len(events) > 1:
        sorted_events = sorted(events, key=lambda e: e.event_time)
        window = []
        for event in sorted_events:
            window.append(event)
            if len(window) > 1:
                prev = window[-2]
                delta = (event.event_time - prev.event_time).total_seconds()
                if delta <= 300:
                    burst_count += 1

    gaps = []
    for i in range(1, len(events)):
        prev = events[i - 1]
        current = events[i]
        delta = (current.event_time - prev.event_time).total_seconds()
        if delta > 0:
            gaps.append(delta / 60.0)

    offline_gap_minutes = max(gaps) if gaps else 0.0
    context_switches = len(set(e.task_context for e in events if e.task_context)) if any(e.task_context for e in events) else 0

    return {
        "median_response_latency_ms": float(median(latencies)) if latencies else 0.0,
        "response_variance": float(response_variance),
        "message_burst_count": float(burst_count),
        "voice_note_ratio": float(sum(1 for e in events if e.event_type in {"voice_note", "voice"}) / len(events)) if events else 0.0,
        "task_ack_lag_ms": float(_safe_mean(latencies)) if latencies else 0.0,
        "hour_of_day": float(_safe_mean(event_hours)) if event_hours else 0.0,
        "day_of_week": float(_safe_mean(event_days)) if event_days else 0.0,
        "urgency_score": float(_safe_mean(urgencies)) if urgencies else 0.0,
        "recovery_lag_ms": float(_safe_mean(latencies)) if latencies else 0.0,
        "context_switches": float(context_switches),
        "offline_gap_minutes": float(offline_gap_minutes),
        "presence_confidence": float(min(1.0, max(0.2, 1.0 - (offline_gap_minutes / 600.0)))) if events else 0.0,
    }
