import requests

USGS_ELEVATION_URL = "https://epqs.nationalmap.gov/v1/json"
HEADERS = {"User-Agent": "GroundTruthMDC/1.0"}


def get_elevation(lon, lat):
    """Query USGS for elevation at a point. Returns elevation in feet."""
    params = {
        "x": str(lon),
        "y": str(lat),
        "wkid": "4326",
        "units": "Feet",
        "includeDate": "false",
    }

    try:
        resp = requests.get(USGS_ELEVATION_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        elevation = data.get("value")
        if elevation is not None:
            elevation = round(float(elevation), 1)
        return {
            "elevation_ft": elevation,
            "source": "USGS National Map",
        }
    except (requests.RequestException, ValueError, TypeError):
        return {
            "elevation_ft": None,
            "source": "unavailable",
            "error": "Could not query elevation data",
        }
