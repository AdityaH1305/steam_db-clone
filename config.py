"""Centralised configuration — reads from .env or environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask ──────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "steamdb-dev-key")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "1") == "1"

    # ── Steam API ─────────────────────────────────────────
    STEAM_API_TIMEOUT: int = int(os.getenv("STEAM_API_TIMEOUT", "10"))
    STEAM_REVIEW_TIMEOUT: int = int(os.getenv("STEAM_REVIEW_TIMEOUT", "12"))
    USER_AGENT: str = "Mozilla/5.0 (SteamDB-Clone ValueScore)"

    # ── Cache TTLs (seconds) ──────────────────────────────
    CACHE_TTL_APPDETAILS: int = int(os.getenv("CACHE_TTL_APPDETAILS", "300"))
    CACHE_TTL_REVIEWS: int = int(os.getenv("CACHE_TTL_REVIEWS", "120"))
    CACHE_TTL_PRICES: int = int(os.getenv("CACHE_TTL_PRICES", "300"))
    CACHE_MAXSIZE: int = int(os.getenv("CACHE_MAXSIZE", "4096"))

    # ── Parallel fetching ─────────────────────────────────
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "10"))

    # ── Data paths ────────────────────────────────────────
    GAMES_JSON: str = os.getenv("GAMES_JSON", "games.json")

    # ── Regions for price comparison ──────────────────────
    REGIONS: list[str] = [
        "us", "gb", "eu", "in", "ae", "ca", "au", "jp", "kr", "br",
    ]

    CURRENCY_SYMBOLS: dict[str, str] = {
        "USD": "$", "GBP": "£", "EUR": "€", "INR": "₹", "AED": "د.إ",
        "CAD": "C$", "AUD": "A$", "JPY": "¥", "KRW": "₩", "BRL": "R$",
    }

    REGION_FLAGS: dict[str, str] = {
        "US": "🇺🇸", "GB": "🇬🇧", "EU": "🇪🇺", "IN": "🇮🇳", "AE": "🇦🇪",
        "CA": "🇨🇦", "AU": "🇦🇺", "JP": "🇯🇵", "KR": "🇰🇷", "BR": "🇧🇷",
    }

    REGION_NAMES: dict[str, str] = {
        "US": "USA", "GB": "UK", "EU": "Europe", "IN": "India", "AE": "UAE",
        "CA": "Canada", "AU": "Australia", "JP": "Japan", "KR": "Korea", "BR": "Brazil",
    }

    # ── Approximate USD exchange rates (for comparison) ───
    # Updated periodically; these are rough mid-market rates
    USD_RATES: dict[str, float] = {
        "USD": 1.0, "GBP": 1.27, "EUR": 1.08, "INR": 0.012,
        "AED": 0.27, "CAD": 0.74, "AUD": 0.65, "JPY": 0.0067,
        "KRW": 0.00075, "BRL": 0.20,
    }

    # ── Trending – curated popular appids ─────────────────
    TRENDING_APPIDS: list[str] = [
        "730",      # Counter-Strike 2
        "570",      # Dota 2
        "440",      # Team Fortress 2
        "1091500",  # Cyberpunk 2077
        "1174180",  # Red Dead Redemption 2
        "892970",   # Valheim
        "1245620",  # Elden Ring
        "413150",   # Stardew Valley
        "814380",   # Sekiro
        "1086940",  # Baldur's Gate 3
        "367520",   # Hollow Knight
        "291550",   # Brawlhalla
        "105600",   # Terraria
        "252490",   # Rust
        "578080",   # PUBG
        "1172470",  # Apex Legends
        "1238810",  # PowerWash Simulator
        "1222670",  # The Sims 4
        "1203220",  # NARAKA
        "2358720",  # Black Myth: Wukong
    ]
