import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from risk_engine import build_risk_profile
from translator import get_risk_summary

load_dotenv()

app = Flask(__name__)

# Simple in-memory cache
_cache = {}

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode_address(address):
    """Geocode an address using Nominatim. Returns (lat, lon) or None."""
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "us",
        "viewbox": "-80.87,25.98,-80.05,25.24",
        "bounded": 1,
    }
    headers = {"User-Agent": "GroundTruthMDC/1.0"}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/geocode", methods=["GET"])
def api_geocode():
    address = request.args.get("address", "").strip()
    if not address:
        return jsonify({"error": "Address is required"}), 400

    result = geocode_address(address)
    if result is None:
        return jsonify({"error": "Could not geocode address. Try a more specific Miami-Dade address."}), 404

    lat, lon = result
    return jsonify({"lat": lat, "lon": lon, "address": address})


@app.route("/api/risk", methods=["GET"])
def api_risk():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid lat and lon parameters are required"}), 400

    address = request.args.get("address", f"{lat:.4f}, {lon:.4f}")

    # Check cache
    cache_key = f"{lat:.5f},{lon:.5f}"
    if cache_key in _cache:
        profile = _cache[cache_key]
        profile["address"] = address
    else:
        profile = build_risk_profile(lon, lat, address)
        _cache[cache_key] = profile

    # Get AI summary (not cached — it's cheap and address may differ)
    summary = get_risk_summary(profile)
    profile["ai_summary"] = summary

    return jsonify(profile)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
