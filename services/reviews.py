"""Review statistics service.

Computes positivity, total reviews, and median/p75 playtime from
Steam's review API.  All heavy work is done through the shared
:mod:`steam_api` layer (cached + pooled).
"""

from __future__ import annotations

import statistics
from typing import Any

from config import Config
from services.steam_api import get_reviews_page, get_review_summary


def _extract_hours(reviews: list[dict]) -> dict[str, float]:
    """Pull median and p75 playtime (in hours) from a reviews list."""
    mins = [
        rev.get("author", {}).get("playtime_forever", 0)
        for rev in reviews
    ]
    hrs = sorted(m / 60.0 for m in mins if isinstance(m, (int, float)) and m >= 0)
    if not hrs:
        return {"p50": 0.0, "p75": 0.0}

    p50 = statistics.median(hrs)
    idx75 = max(0, min(len(hrs) - 1, int(round(0.75 * (len(hrs) - 1)))))
    p75 = hrs[idx75]
    return {"p50": float(p50), "p75": float(p75)}


def get_review_stats(appid: str) -> dict[str, Any]:
    """Return review statistics for *appid*.

    Keys: ``positivity``, ``total_reviews``, ``total_positive``,
    ``total_negative``, ``p50_all``, ``p50_recent``, ``p75_recent``,
    ``recent_positivity``.
    """
    positivity = 0.0
    total = 0
    total_positive = 0
    total_negative = 0
    p50_all = p50_recent = p75_recent = 0.0
    recent_positivity = 0.0

    # 1) Summary for overall positivity + totals
    q = get_review_summary(appid)
    if q:
        pos = float(q.get("total_positive", 0))
        neg = float(q.get("total_negative", 0))
        total_positive = int(pos)
        total_negative = int(neg)
        total = int(pos + neg)
        positivity = (pos / (pos + neg)) if (pos + neg) > 0 else 0.0

    # 2) One page of ALL reviews → long-term median
    reviews_all = get_reviews_page(appid, "all")
    if reviews_all:
        stats_all = _extract_hours(reviews_all)
        p50_all = stats_all["p50"]

    # 3) One page of RECENT reviews → current playtime & recent positivity
    reviews_recent = get_reviews_page(appid, "recent")
    if reviews_recent:
        stats_recent = _extract_hours(reviews_recent)
        p50_recent = stats_recent["p50"]
        p75_recent = stats_recent["p75"]
        # Compute recent-only positivity
        rp = sum(1 for r in reviews_recent if r.get("voted_up"))
        rn = len(reviews_recent)
        recent_positivity = (rp / rn) if rn > 0 else 0.0

    return {
        "positivity": positivity,
        "total_reviews": total,
        "total_positive": total_positive,
        "total_negative": total_negative,
        "p50_all": p50_all,
        "p50_recent": p50_recent,
        "p75_recent": p75_recent,
        "recent_positivity": recent_positivity,
    }
