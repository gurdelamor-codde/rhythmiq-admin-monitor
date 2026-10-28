def infer_state(features: dict) -> str:
    if not features or not any(v != 0 for v in features.values()):
        return "UNKNOWN"

    if features["median_response_latency_ms"] < 180000 and features["context_switches"] < 3 and features["offline_gap_minutes"] < 30:
        return "FOCUSED"

    if features["response_variance"] > 0.75 or features["urgency_score"] > 0.8:
        if features["urgency_score"] > 0.8:
            return "REACTING"
        return "OVERLOADED"

    if features["message_burst_count"] <= 2 and features["offline_gap_minutes"] > 60:
        return "AVAILABLE"

    return "STABLE"
