"""SteamDB Clone — Flask Application.

Slim route layer.  All business logic lives in ``/services``.
"""

from __future__ import annotations

from flask import Flask, render_template, request, jsonify, redirect, url_for

from config import Config
from services.search import find_matches, find_appid_by_name
from services.pricing import fetch_all_prices, get_usd_price
from services.reviews import get_review_stats
from services.value_score import compute_value_score
from services.vibes import VIBES, score_vibes_for_app, discover_by_vibes
from services.recommendations import get_recommendations

# ── App factory ───────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)


# ── Template helpers ──────────────────────────────────────
@app.context_processor
def inject_helpers():
    def get_symbol(code: str) -> str:
        return Config.CURRENCY_SYMBOLS.get(code.upper(), "")

    def get_flag(region: str) -> str:
        return Config.REGION_FLAGS.get(region.upper(), "🌐")

    def get_region_name(region: str) -> str:
        return Config.REGION_NAMES.get(region.upper(), region.upper())

    return dict(
        get_symbol=get_symbol,
        get_flag=get_flag,
        get_region_name=get_region_name,
    )


# ══════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════

@app.route("/")
def home():
    """Home page — search form."""
    return render_template("index.html")


@app.route("/game", methods=["POST"])
def game_post():
    """Handle the search form POST — resolve appid then redirect to GET."""
    selected_appid = request.form.get("game_input_id", "").strip()
    game_input = request.form.get("game_input", "").strip()

    appid = None
    if selected_appid and selected_appid.isdigit():
        appid = selected_appid
    else:
        raw = game_input.lower()
        if raw.isdigit():
            appid = raw
        else:
            appid = find_appid_by_name(raw)
            if not appid:
                return f"❌ Game '{game_input}' not found in Steam's app list.", 404

    return redirect(url_for("game_page", appid=appid))


@app.route("/game/<appid>")
def game_page(appid: str):
    """Game detail page (GET — linkable)."""
    price_data = fetch_all_prices(appid)
    all_prices = price_data["prices"]

    if not all_prices:
        return "❌ Price information not available in any region.", 404

    game_name = price_data["game_name"]
    cover_url = price_data["cover_url"]

    # Vibes
    try:
        vibe_info = score_vibes_for_app(appid)
    except Exception:
        vibe_info = {"top": []}

    # Value score
    usd_price = get_usd_price(all_prices)
    stats = get_review_stats(appid)
    value_score, value_label, value_debug = compute_value_score(
        usd_price or 0.0, stats
    )

    return render_template(
        "game.html",
        name=game_name,
        appid=appid,
        all_prices=all_prices,
        cover_url=cover_url,
        store_url=f"https://store.steampowered.com/app/{appid}",
        value_score=value_score,
        value_label=value_label,
        stats=stats,
        usd_price=usd_price,
        value_debug=value_debug,
        vibe_info=vibe_info,
        cheapest=price_data["cheapest"],
    )


@app.route("/moods")
def moods_page():
    """Interactive mood / vibe discovery page."""
    mood_list = [
        {"key": k, "label": v["label"], "emoji": v["emoji"]}
        for k, v in VIBES.items()
    ]
    mood_list.sort(key=lambda x: x["label"])
    return render_template("moods.html", moods=mood_list)


@app.route("/trending")
def trending_page():
    """Trending / popular games page."""
    return render_template("trending.html")


@app.route("/compare")
def compare_page():
    """Compare multiple games side-by-side."""
    return render_template("compare.html")


# ══════════════════════════════════════════════════════════
#  API ROUTES
# ══════════════════════════════════════════════════════════

@app.route("/autocomplete")
def autocomplete():
    """AJAX autocomplete endpoint (backwards compatible)."""
    q = request.args.get("q", "")
    return jsonify(find_matches(q, limit=8))


@app.route("/api/search")
def api_search():
    """Search endpoint — richer than autocomplete."""
    q = request.args.get("q", "")
    limit = request.args.get("limit", "10", type=str)
    try:
        limit_int = int(limit)
    except ValueError:
        limit_int = 10
    return jsonify(find_matches(q, limit=min(limit_int, 20)))


@app.route("/api/game/<appid>")
def api_game(appid: str):
    """Full game data bundle."""
    price_data = fetch_all_prices(appid)
    all_prices = price_data["prices"]
    usd_price = get_usd_price(all_prices)
    stats = get_review_stats(appid)
    value_score, value_label, value_debug = compute_value_score(
        usd_price or 0.0, stats
    )
    try:
        vibe_info = score_vibes_for_app(appid)
    except Exception:
        vibe_info = {"top": []}

    return jsonify({
        "appid": appid,
        "name": price_data["game_name"],
        "cover_url": price_data["cover_url"],
        "store_url": f"https://store.steampowered.com/app/{appid}",
        "prices": all_prices,
        "cheapest": price_data["cheapest"],
        "usd_price": usd_price,
        "reviews": stats,
        "value_score": value_score,
        "value_label": value_label,
        "value_breakdown": value_debug,
        "vibes": vibe_info,
    })


@app.route("/api/prices/<appid>")
def api_prices(appid: str):
    """Regional prices for *appid*."""
    return jsonify(fetch_all_prices(appid))


@app.route("/api/value/<appid>")
def api_value(appid: str):
    """Value score for *appid*."""
    price_data = fetch_all_prices(appid)
    usd_price = get_usd_price(price_data["prices"])
    stats = get_review_stats(appid)
    score, label, breakdown = compute_value_score(usd_price or 0.0, stats)
    return jsonify({
        "appid": appid,
        "score": score,
        "label": label,
        "breakdown": breakdown,
        "reviews": stats,
        "usd_price": usd_price,
    })


@app.route("/api/recommendations/<appid>")
def api_recommendations(appid: str):
    """Similar games for *appid*."""
    return jsonify(get_recommendations(appid))


@app.route("/api/vibes/<appid>")
def api_vibes(appid: str):
    """Vibe scores for *appid* (backward compatible)."""
    try:
        return jsonify(score_vibes_for_app(appid))
    except Exception as exc:
        print("vibes error", exc)
        return jsonify({"error": "vibe_failed"}), 500


@app.route("/api/discover")
def api_discover():
    """Discover games by mood (backward compatible)."""
    mood_keys = [m for m in request.args.getlist("m") if m in VIBES]
    if not mood_keys:
        return jsonify([])
    return jsonify(discover_by_vibes(mood_keys, limit=18))


@app.route("/api/trending")
def api_trending():
    """Return trending game data (curated list)."""
    from services.steam_api import get_appdetails, executor

    appids = Config.TRENDING_APPIDS

    def _fetch_trending_item(aid: str) -> dict | None:
        data = get_appdetails(aid, cc="us")
        if not data or not data.get("name"):
            return None
        price_info = data.get("price_overview")
        price_str = "Free to Play"
        if price_info:
            price_str = price_info.get("final_formatted", f"${price_info['final']/100:.2f}")
        return {
            "appid": aid,
            "name": data["name"],
            "cover": data.get("header_image", f"https://cdn.cloudflare.steamstatic.com/steam/apps/{aid}/header.jpg"),
            "short_description": (data.get("short_description") or "")[:120],
            "price": price_str,
            "genres": [g["description"] for g in (data.get("genres") or [])[:3]],
        }

    results = list(executor.map(_fetch_trending_item, appids))
    return jsonify([r for r in results if r])


# ══════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════
#Final Run
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
