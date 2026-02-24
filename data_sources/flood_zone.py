import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

FEMA_NATIONAL_URL = (
    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
)

ZONE_RISK = {
    "V": "Coastal High Hazard",
    "VE": "Coastal High Hazard",
    "A": "High Risk",
    "AE": "High Risk",
    "AH": "High Risk (Shallow Flooding)",
    "AO": "High Risk (Sheet Flow)",
    "AR": "High Risk (Restored)",
    "A99": "High Risk (Future Conditions)",
    "X": "Moderate to Low Risk",
    "B": "Moderate Risk",
    "C": "Low Risk",
    "D": "Undetermined",
}

HEADERS = {"User-Agent": "GroundTruthMDC/1.0"}


def _get_session():
    session = requests.Session()
    retries = Retry(total=2, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def get_flood_zone(lon, lat):
    """Query FEMA flood zone for a coordinate. Returns dict with zone info."""
    params = {
        "geometry": f'{{"x":{lon},"y":{lat}}}',
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,ZONE_SUBTY,STATIC_BFE",
        "returnGeometry": "false",
        "f": "json",
    }

    try:
        session = _get_session()
        resp = session.get(FEMA_NATIONAL_URL, params=params, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if features:
            attrs = features[0]["attributes"]
            zone = attrs.get("FLD_ZONE", "Unknown")
            return {
                "zone": zone,
                "zone_subtype": attrs.get("ZONE_SUBTY", ""),
                "base_flood_elevation": attrs.get("STATIC_BFE"),
                "risk_level": ZONE_RISK.get(zone, "Unknown"),
                "source": "FEMA NFHL",
            }
    except (requests.RequestException, KeyError, IndexError):
        pass

    return {
        "zone": "Unknown",
        "zone_subtype": "",
        "base_flood_elevation": None,
        "risk_level": "Unable to determine",
        "source": "unavailable",
        "error": "Could not query flood zone data",
    }
