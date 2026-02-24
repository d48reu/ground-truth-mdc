import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

NOAA_SLR_BASE = "https://coast.noaa.gov/arcgis/rest/services/dc_slr"

# NOAA medium projection timeline (approximate)
SLR_YEAR_ESTIMATE = {
    1: "~2040",
    2: "~2060",
    3: "~2080",
    4: "~2100",
    5: "~2120",
    6: "~2150",
}

MAX_CHECK_FT = 6  # Check 1ft through 6ft
HEADERS = {"User-Agent": "GroundTruthMDC/1.0"}


def _check_inundation(level_ft, lon, lat):
    """Check if a point is inundated at a given sea level rise amount."""
    url = f"{NOAA_SLR_BASE}/slr_{level_ft}ft/MapServer/0/query"
    params = {
        "geometry": f'{{"x":{lon},"y":{lat}}}',
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "returnCountOnly": "true",
        "f": "json",
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        count = data.get("count", 0)
        return level_ft, count > 0
    except (requests.RequestException, ValueError):
        return level_ft, None


def get_sea_level_rise(lon, lat):
    """Check sea level rise inundation from 1ft to 6ft. Returns first level that floods."""
    results = {}

    with ThreadPoolExecutor(max_workers=MAX_CHECK_FT) as executor:
        futures = {
            executor.submit(_check_inundation, ft, lon, lat): ft
            for ft in range(1, MAX_CHECK_FT + 1)
        }
        for future in as_completed(futures):
            level, inundated = future.result()
            results[level] = inundated

    # Find the lowest level that causes inundation
    first_inundation = None
    levels_checked = {}
    for ft in range(1, MAX_CHECK_FT + 1):
        inundated = results.get(ft)
        levels_checked[f"{ft}ft"] = inundated
        if inundated and first_inundation is None:
            first_inundation = ft

    return {
        "first_inundation_ft": first_inundation,
        "projected_year": SLR_YEAR_ESTIMATE.get(first_inundation, "Beyond 2150")
        if first_inundation
        else "Not inundated at 6ft",
        "levels_checked": levels_checked,
        "source": "NOAA Sea Level Rise Viewer",
    }
