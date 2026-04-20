from __future__ import annotations

import time
from collections import Counter, deque
from statistics import mean
from typing import TypedDict

# ── Metrics Configuration ─────────────────────────────────────
MAX_SAMPLES = 200  # Number of samples for latency/quality moving windows
MAX_HISTORY = 60   # Number of points in time-series (15s intervals)

# ── Windowed Metrics (Real-time sliding windows) ─────────────
# Distributions use a simple sample-based window
REQUEST_LATENCIES: deque[int] = deque(maxlen=MAX_SAMPLES)
QUALITY_SCORES: deque[float] = deque(maxlen=MAX_SAMPLES)

# Counters use a time-based window (last 60 seconds)
# Each entry is (timestamp, value)
_TRAFFIC_SAMPLES: deque[tuple[float, int]] = deque()
_COST_SAMPLES: deque[tuple[float, float]] = deque()
_TOKENS_IN_SAMPLES: deque[tuple[float, int]] = deque()
_TOKENS_OUT_SAMPLES: deque[tuple[float, int]] = deque()

# Totals (all-time tracking)
TRAFFIC_TOTAL: int = 0
COST_TOTAL: float = 0.0
TOKENS_IN_TOTAL: int = 0
TOKENS_OUT_TOTAL: int = 0
ERRORS_TOTAL: Counter[str] = Counter()

# Previous totals for history delta calculation
_prev_traffic: int = 0
_prev_cost: float = 0.0
_prev_tokens_in: int = 0
_prev_tokens_out: int = 0
_prev_errors: int = 0

class HistoryPoint(TypedDict):
    ts: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    traffic: int           # Traffic in this interval
    error_rate_pct: float  # Error rate in this interval
    total_cost_usd: float  # Cost in this interval
    tokens_in: int         # Tokens in in this interval
    tokens_out: int        # Tokens out in this interval
    quality_avg: float     # Windowed average quality at this moment

HISTORY: deque[HistoryPoint] = deque(maxlen=MAX_HISTORY)


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    global TRAFFIC_TOTAL, COST_TOTAL, TOKENS_IN_TOTAL, TOKENS_OUT_TOTAL
    now = time.time()
    
    # Update totals
    TRAFFIC_TOTAL += 1
    COST_TOTAL += cost_usd
    TOKENS_IN_TOTAL += tokens_in
    TOKENS_OUT_TOTAL += tokens_out
    
    # Update windowed samples
    _TRAFFIC_SAMPLES.append((now, 1))
    _COST_SAMPLES.append((now, cost_usd))
    _TOKENS_IN_SAMPLES.append((now, tokens_in))
    _TOKENS_OUT_SAMPLES.append((now, tokens_out))
    
    REQUEST_LATENCIES.append(latency_ms)
    QUALITY_SCORES.append(quality_score)
    
    # Prune old samples (> 60s)
    _prune_samples(now)


def _prune_samples(now: float) -> None:
    cutoff = now - 60
    while _TRAFFIC_SAMPLES and _TRAFFIC_SAMPLES[0][0] < cutoff: _TRAFFIC_SAMPLES.popleft()
    while _COST_SAMPLES and _COST_SAMPLES[0][0] < cutoff: _COST_SAMPLES.popleft()
    while _TOKENS_IN_SAMPLES and _TOKENS_IN_SAMPLES[0][0] < cutoff: _TOKENS_IN_SAMPLES.popleft()
    while _TOKENS_OUT_SAMPLES and _TOKENS_OUT_SAMPLES[0][0] < cutoff: _TOKENS_OUT_SAMPLES.popleft()


def record_error(error_type: str) -> None:
    ERRORS_TOTAL[error_type] += 1


def percentile(values: deque[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(list(values))
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])


def snapshot() -> dict:
    """Returns the CURRENT state of metrics. 
    Now returns windowed (last 60s) values for traffic, cost, and tokens."""
    _prune_samples(time.time())
    
    traffic_now = sum(s[1] for s in _TRAFFIC_SAMPLES)
    cost_now = sum(s[1] for s in _COST_SAMPLES)
    tokens_in_now = sum(s[1] for s in _TOKENS_IN_SAMPLES)
    tokens_out_now = sum(s[1] for s in _TOKENS_OUT_SAMPLES)
    
    total_errs = sum(ERRORS_TOTAL.values())
    error_rate = round((total_errs / TRAFFIC_TOTAL * 100), 2) if TRAFFIC_TOTAL > 0 else 0.0
    
    return {
        "traffic": traffic_now,
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "total_cost_usd": round(cost_now, 6),
        "tokens_in_total": tokens_in_now,
        "tokens_out_total": tokens_out_now,
        "error_breakdown": dict(ERRORS_TOTAL),
        "error_rate_pct": error_rate,
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
        "absolute_totals": {
            "traffic": TRAFFIC_TOTAL,
            "cost": round(COST_TOTAL, 6),
            "tokens_in": TOKENS_IN_TOTAL,
            "tokens_out": TOKENS_OUT_TOTAL
        }
    }


def push_history() -> None:
    """
    Called periodically (e.g., every 15s) to record a 'real-time' interval.
    Calculates deltas since the last call so charts show per-interval activity.
    """
    global _prev_traffic, _prev_cost, _prev_tokens_in, _prev_tokens_out, _prev_errors
    
    # Capture current state
    curr_traffic = TRAFFIC_TOTAL
    curr_cost = COST_TOTAL
    curr_tokens_in = TOKENS_IN_TOTAL
    curr_tokens_out = TOKENS_OUT_TOTAL
    curr_errors = sum(ERRORS_TOTAL.values())
    
    # Calculate deltas (the 'real-time' part)
    delta_traffic = curr_traffic - _prev_traffic
    delta_cost = curr_cost - _prev_cost
    delta_tokens_in = curr_tokens_in - _prev_tokens_in
    delta_tokens_out = curr_tokens_out - _prev_tokens_out
    delta_errors = curr_errors - _prev_errors
    
    # Interval error rate
    interval_error_rate = round((delta_errors / delta_traffic * 100), 2) if delta_traffic > 0 else 0.0
    
    # Store history point
    HISTORY.append(HistoryPoint(
        ts=time.time(),
        latency_p50=percentile(REQUEST_LATENCIES, 50),
        latency_p95=percentile(REQUEST_LATENCIES, 95),
        latency_p99=percentile(REQUEST_LATENCIES, 99),
        traffic=delta_traffic,
        error_rate_pct=interval_error_rate,
        total_cost_usd=round(delta_cost, 6),
        tokens_in=delta_tokens_in,
        tokens_out=delta_tokens_out,
        quality_avg=round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    ))
    
    # Update previous markers
    _prev_traffic = curr_traffic
    _prev_cost = curr_cost
    _prev_tokens_in = curr_tokens_in
    _prev_tokens_out = curr_tokens_out
    _prev_errors = curr_errors


def get_history() -> list[HistoryPoint]:
    return list(HISTORY)