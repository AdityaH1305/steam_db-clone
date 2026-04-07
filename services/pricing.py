"""Regional pricing service.

Rewritten to use the shared ``get_appdetails()`` cache instead of making
raw HTTP calls — eliminates 10 duplicate API requests per game page load.
"""

from __future__ import annotations

from typing import Any

from config import Config
from services.steam_api import get_appdetails, executor


def _extract_price_for_region(
    appid: str, cc: str
) -> tuple[dict | None, str | None, str | None]:
    """Extract price from the *cached* appdetails response for one region."""
    game_data = get_appdetails(appid, cc=cc)
    if not game_data:
        return None, None, None

    price_info = game_data.get("price_overview")

    if not price_info:
        is_free = game_data.get("is_free", False)
        if is_free:
            currency_price: dict[str, Any] = {
                "region": cc.upper(),
                "currency": "USD",
                "initial": 0,
                "final": 0,
                "discount": 0,
                "is_free": True,
            }
        else:
            return None, None, None
    else:
        currency_price: dict[str, Any] = {
            "region": cc.upper(),
            "currency": price_info["currency"],
            "initial": price_info["initial"] / 100,
            "final": price_info["final"] / 100,
            "discount": price_info["discount_percent"],
        }

    cover_url = (
        game_data.get("header_image")
        or f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"
    )
    game_name = game_data.get("name", "Unknown Game")
    return currency_price, game_name, cover_url


def fetch_all_prices(appid: str) -> dict[str, Any]:
    """Fetch prices across all configured regions in parallel.

    Now uses the shared cached ``get_appdetails()`` layer, so repeated
    calls (from vibes, recommendations, etc.) hit cache instead of the
    network.
    """
    regions = Config.REGIONS
    futures = executor.map(
        lambda cc: _extract_price_for_region(appid, cc), regions
    )

    all_prices: list[dict] = []
    game_name = "Unknown Game"
    cover_url: str | None = None

    for currency_price, g_name, c_url in futures:
        if not currency_price:
            continue
        all_prices.append(currency_price)
        if game_name == "Unknown Game" and g_name:
            game_name = g_name
        if cover_url is None and c_url:
            cover_url = c_url

    # ── USD conversion & cheapest detection ───────────────
    cheapest: dict | None = None
    cheapest_usd = float("inf")

    for p in all_prices:
        rate = Config.USD_RATES.get(p["currency"], 1.0)
        usd_equiv = p["final"] * rate
        p["usd_equivalent"] = round(usd_equiv, 2)

        if usd_equiv > 0 and usd_equiv < cheapest_usd:
            cheapest_usd = usd_equiv
            cheapest = p

    # Mark cheapest & compute % diff vs US price
    us_price_usd: float | None = None
    for p in all_prices:
        if p["region"] == "US":
            us_price_usd = p["usd_equivalent"]
            break

    for p in all_prices:
        p["is_cheapest"] = (cheapest is not None and p["region"] == cheapest["region"])
        if us_price_usd and us_price_usd > 0:
            diff = ((p["usd_equivalent"] - us_price_usd) / us_price_usd) * 100
            p["vs_usd_pct"] = round(diff, 1)
        else:
            p["vs_usd_pct"] = 0.0

    if not cover_url:
        cover_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"

    return {
        "game_name": game_name,
        "cover_url": cover_url,
        "prices": all_prices,
        "cheapest": cheapest,
    }


def get_usd_price(prices: list[dict]) -> float | None:
    """Extract USD final price from a prices list."""
    for p in prices:
        if p.get("currency") == "USD":
            return p["final"]
    if prices:
        return prices[0]["final"]
    return None
