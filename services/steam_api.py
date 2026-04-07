"""Thin wrapper around the Steam Store & Review APIs.

Provides:
- A shared ``requests.Session`` with connection pooling.
- ``fetch_appdetails(appid, cc)`` with TTL-aware LRU cache.
- ``fetch_reviews_page(appid, filt)`` with TTL-aware LRU cache.
- A shared ``ThreadPoolExecutor`` for parallel work.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any

import requests as _requests

from config import Config

# ── Shared resources ──────────────────────────────────────
_session = _requests.Session()
_session.headers.update({"User-Agent": Config.USER_AGENT})

executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS)

# ── TTL-aware caching helpers ─────────────────────────────
# We wrap lru_cache with a generation counter that ticks
# every TTL seconds so stale entries are evicted naturally.

def _ttl_key(ttl: int) -> int:
    """Return a generation number that changes every *ttl* seconds."""
    return int(time.time() // ttl)


@lru_cache(maxsize=Config.CACHE_MAXSIZE)
def fetch_appdetails(appid: str, cc: str = "us", _gen: int = 0) -> dict[str, Any]:
    """Fetch ``/api/appdetails`` for *appid* using country code *cc*.

    The ``_gen`` parameter is filled automatically and should NOT be
    passed by callers — use :func:`get_appdetails` instead.
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={cc}"
    try:
        r = _session.get(url, timeout=Config.STEAM_API_TIMEOUT)
        r.raise_for_status()
        node = r.json().get(str(appid), {})
        return node.get("data") or {}
    except Exception as exc:
        print(f"[steam_api] appdetails error ({appid}, {cc}): {exc}")
        return {}


def get_appdetails(appid: str, cc: str = "us") -> dict[str, Any]:
    """Public helper — injects TTL generation so cache auto-expires."""
    return fetch_appdetails(appid, cc, _gen=_ttl_key(Config.CACHE_TTL_APPDETAILS))


@lru_cache(maxsize=2048)
def fetch_reviews_page(appid: str, filt: str = "recent", _gen: int = 0) -> list[dict]:
    """Return one page (up to 100) of reviews for *appid*."""
    base = (
        f"https://store.steampowered.com/appreviews/{appid}?json=1"
        f"&language=all&purchase_type=all&num_per_page=100&filter={filt}"
    )
    try:
        r = _session.get(base, timeout=Config.STEAM_REVIEW_TIMEOUT)
        r.raise_for_status()
        return (r.json() or {}).get("reviews", []) or []
    except Exception as exc:
        print(f"[steam_api] reviews error ({appid}, {filt}): {exc}")
        return []


def get_reviews_page(appid: str, filt: str = "recent") -> list[dict]:
    """Public helper — injects TTL generation for cache auto-expiry."""
    return fetch_reviews_page(appid, filt, _gen=_ttl_key(Config.CACHE_TTL_REVIEWS))


@lru_cache(maxsize=2048)
def _fetch_review_summary(appid: str, _gen: int = 0) -> dict[str, Any]:
    """Fetch the review *summary* (positivity + totals) — cached."""
    url = (
        f"https://store.steampowered.com/appreviews/{appid}?json=1"
        f"&filter=summary&language=all&purchase_type=all&num_per_page=0"
    )
    try:
        r = _session.get(url, timeout=Config.STEAM_API_TIMEOUT)
        r.raise_for_status()
        return r.json().get("query_summary", {}) or {}
    except Exception as exc:
        print(f"[steam_api] review summary error ({appid}): {exc}")
        return {}


def get_review_summary(appid: str) -> dict[str, Any]:
    """Public helper — injects TTL generation for cache auto-expiry."""
    return _fetch_review_summary(appid, _gen=_ttl_key(Config.CACHE_TTL_REVIEWS))
