"""Game search & autocomplete service.

Loads ``games.json`` once at import time and builds prefix indices for
fast lookup.  The fuzzy-matching algorithm is preserved from the
original ``app.py`` — it supports acronyms, prefix matches, substring
matches, and RapidFuzz token-set-ratio scoring.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any

from config import Config

# ── Optional RapidFuzz ────────────────────────────────────
try:
    from rapidfuzz import fuzz
    _RF_AVAILABLE = True
except ImportError:
    _RF_AVAILABLE = False

import difflib

# ── Text normalisation ────────────────────────────────────
_norm_re = re.compile(r"[^a-z0-9]+")


def _normalize(s: str) -> str:
    s = (s or "").lower()
    s = _norm_re.sub(" ", s).strip()
    return re.sub(r"\s+", " ", s)


def _tokenize(s: str) -> list[str]:
    return [t for t in _normalize(s).split() if t]


def _acronym(tokens: list[str]) -> str:
    return "".join(t[0] for t in tokens if t)


# ── Load game list ────────────────────────────────────────
def _load_games(filepath: str = Config.GAMES_JSON) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        apps = json.load(f)["applist"]["apps"]

    games: list[dict] = []
    for a in apps:
        name = a.get("name")
        appid = a.get("appid")
        if not name or appid is None:
            continue

        tokens = _tokenize(name)
        games.append({
            "appid": str(appid),
            "name": name,
            "name_low": name.lower(),
            "name_norm": " ".join(tokens),
            "compact": "".join(tokens),
            "acronym": _acronym(tokens),
        })
    return games


GAMES: list[dict] = _load_games()

# Prefix indices (2-char buckets)
PREFIX2_NORM: dict[str, list[dict]] = defaultdict(list)
PREFIX2_COMPACT: dict[str, list[dict]] = defaultdict(list)

for _g in GAMES:
    _kn = _g["name_norm"][:2] if len(_g["name_norm"]) >= 2 else _g["name_norm"]
    _kc = _g["compact"][:2] if len(_g["compact"]) >= 2 else _g["compact"]
    PREFIX2_NORM[_kn].append(_g)
    PREFIX2_COMPACT[_kc].append(_g)


# ── Fuzzy ratio helper ────────────────────────────────────
def _fuzzy_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if _RF_AVAILABLE:
        return float(fuzz.token_set_ratio(a, b))
    return difflib.SequenceMatcher(None, a, b).ratio() * 100.0


# ── Public API ────────────────────────────────────────────

def find_appid_by_name(name_query: str) -> str | None:
    """Return the first matching appid for *name_query* (exact then partial)."""
    q = name_query.lower()
    for g in GAMES:
        if g["name_low"] == q:
            return g["appid"]
    for g in GAMES:
        if q in g["name_low"]:
            return g["appid"]
    return None


def find_matches(query: str, limit: int = 8) -> list[dict[str, str]]:
    """Return up to *limit* matching games for the autocomplete UI.

    Each result is ``{"appid": "...", "name": "..."}``.
    """
    q_raw = (query or "").strip()
    if not q_raw:
        return []

    q_low = q_raw.lower()
    q_norm = _normalize(q_raw)
    q_compact = q_norm.replace(" ", "")
    q2_norm = q_norm[:2]
    q2_comp = q_compact[:2]

    # 1) Collect candidates from prefix indices
    cand: list[dict] = []
    if q2_norm:
        cand += PREFIX2_NORM.get(q2_norm, [])
    if q2_comp:
        cand += PREFIX2_COMPACT.get(q2_comp, [])

    # Broaden if empty
    if not cand and q2_norm:
        for k, lst in PREFIX2_NORM.items():
            if k.startswith(q2_norm[0:1]):
                cand += lst[:150]
                if len(cand) > 400:
                    break

    # 2) Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for g in cand:
        if g["appid"] not in seen:
            seen.add(g["appid"])
            unique.append(g)

    if not unique:
        unique = GAMES[:800]

    # 3) Score each candidate
    scored: list[tuple[float, dict]] = []
    for g in unique:
        name_low = g["name_low"]
        name_norm = g["name_norm"]
        compact = g["compact"]
        acro = g["acronym"]

        prefix = (
            name_low.startswith(q_low)
            or name_norm.startswith(q_norm)
            or compact.startswith(q_compact)
        )
        substr = (not prefix) and (
            q_low in name_low or q_norm in name_norm or q_compact in compact
        )
        acro_hit = (q_compact == acro) or acro.startswith(q_compact)

        fuzzy = max(
            _fuzzy_ratio(q_norm, name_norm),
            _fuzzy_ratio(q_compact, compact),
            _fuzzy_ratio(q_compact, acro),
        )

        score = 0.0
        if acro_hit:
            score += 85
        if prefix:
            score += 60
        elif substr:
            score += 28
        score += fuzzy

        if not (acro_hit or prefix or substr) and fuzzy < 35:
            continue

        scored.append((score, g))

    scored.sort(key=lambda x: (-x[0], len(x[1]["name"]), x[1]["name"]))
    return [{"name": g["name"], "appid": g["appid"]} for _, g in scored[:limit]]
