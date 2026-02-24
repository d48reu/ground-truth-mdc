import math
import requests

FDEP_CLEANUP_URL = (
    "https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/"
    "CLEANUP_SP/MapServer/8/query"
)

SEARCH_RADIUS_METERS = 1609  # 1 mile
HEADERS = {"User-Agent": "GroundTruthMDC/1.0"}


def _haversine_ft(lon1, lat1, lon2, lat2):
    """Distance between two coordinates in feet."""
    R = 20902231  # Earth radius in feet
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_contamination_sites(lon, lat):
    """Query FDEP for contamination/cleanup sites within 1 mile."""
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": str(SEARCH_RADIUS_METERS),
        "units": "esriSRUnit_Meter",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "json",
    }

    try:
        resp = requests.get(FDEP_CLEANUP_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return {
            "total_count": 0,
            "sites": [],
            "by_program": {},
            "nearest": None,
            "error": "Could not query contamination data",
        }

    features = data.get("features", [])
    if not features and "error" in data:
        return {
            "total_count": 0,
            "sites": [],
            "by_program": {},
            "nearest": None,
            "error": f"API error: {data['error'].get('message', 'Unknown')}",
        }

    sites = []
    by_program = {}

    for f in features:
        attrs = f.get("attributes", {})
        geom = f.get("geometry", {})

        program = attrs.get("PROGRAM", "Unknown")
        by_program[program] = by_program.get(program, 0) + 1

        site_lon = geom.get("x")
        site_lat = geom.get("y")
        distance_ft = None
        if site_lon is not None and site_lat is not None:
            distance_ft = round(_haversine_ft(lon, lat, site_lon, site_lat))

        sites.append(
            {
                "name": attrs.get("SITE_NAME", "Unknown"),
                "address": attrs.get("ADDRESS", ""),
                "city": attrs.get("CITY", ""),
                "program": program,
                "program_status": attrs.get("PROGRAM_STATUS", ""),
                "site_status": attrs.get("SITE_STATUS", "Unknown"),
                "distance_ft": distance_ft,
                "lon": site_lon,
                "lat": site_lat,
            }
        )

    # Sort by distance
    sites.sort(key=lambda s: s["distance_ft"] if s["distance_ft"] is not None else 1e9)

    nearest = sites[0] if sites else None

    return {
        "total_count": len(sites),
        "sites": sites,
        "by_program": by_program,
        "nearest": nearest,
    }
