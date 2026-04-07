"""Value-score computation.

The formula is preserved from the original codebase:
  score = 0.55 × HPD_norm + 0.35 × pos_norm + 0.10 × confidence
where HPD = effective_hours / price, log-normalised.

Enhancements:
- Returns a *breakdown* dict for frontend visualisation.
- Handles free games (price clamped to $1).
- Graceful with low review counts.
"""

from __future__ import annotations

import math
from typing import Any


def compute_value_score(
    usd_price: float, stats: dict[str, Any]
) -> tuple[int, str, dict[str, Any]]:
    """Compute the 0–100 value score.

    Returns ``(score, label, breakdown)``.
    """
    price = max(usd_price or 0.0, 1.0)  # avoid div-by-zero; <$1 → $1
    is_free = (usd_price is not None and usd_price <= 0)

    p50_all = stats.get("p50_all", 0.0)
    p50_recent = stats.get("p50_recent", 0.0)
    p75_recent = stats.get("p75_recent", 0.0)
    positivity = float(stats.get("positivity", 0.0))
    total_rev = int(stats.get("total_reviews", 0))

    # Robust hours signal
    effective_hours = max(p50_all, 0.7 * p75_recent, p50_recent)

    # Hours per dollar
    hpd = effective_hours / price

    # Log normalisation  (hpd 0..20+ → 0..1)
    hpd_norm = (
        math.log10(hpd + 1.0) / math.log10(20.0) if hpd > 0 else 0.0
    )
    hpd_norm = max(0.0, min(1.0, hpd_norm))

    # Positivity above 60 % gets credit
    pos_norm = (positivity - 0.60) / 0.40
    pos_norm = max(0.0, min(1.0, pos_norm))

    # Confidence by review volume
    conf = min(1.0, math.log10(max(10, total_rev)) / 3.0)

    # Weighted blend
    raw = 0.55 * hpd_norm + 0.35 * pos_norm + 0.10 * conf

    # Free games: boost slightly (great value by definition)
    if is_free and positivity > 0.5:
        raw = max(raw, 0.60 + 0.30 * pos_norm + 0.10 * conf)

    score = int(round(max(0.0, min(100.0, 100.0 * raw))))

    # Label
    if score >= 85:
        label = "Excellent value"
    elif score >= 70:
        label = "Great value"
    elif score >= 55:
        label = "Good value"
    elif score >= 40:
        label = "Fair value"
    else:
        label = "Poor value"

    breakdown = {
        "effective_hours": round(effective_hours, 1),
        "hpd": round(hpd, 2),
        "hpd_norm": round(hpd_norm, 3),
        "pos_norm": round(pos_norm, 3),
        "conf": round(conf, 3),
        # Contribution percentages for the bar chart
        "playtime_pct": round(0.55 * hpd_norm * 100, 1),
        "positivity_pct": round(0.35 * pos_norm * 100, 1),
        "confidence_pct": round(0.10 * conf * 100, 1),
        "is_free": is_free,
    }

    return score, label, breakdown
