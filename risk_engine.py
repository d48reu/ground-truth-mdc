from concurrent.futures import ThreadPoolExecutor, as_completed
from data_sources.flood_zone import get_flood_zone
from data_sources.contamination import get_contamination_sites
from data_sources.elevation import get_elevation
from data_sources.sea_level import get_sea_level_rise


def build_risk_profile(lon, lat, address=""):
    """Query all 4 data sources in parallel and combine into a risk profile."""
    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(get_flood_zone, lon, lat): "flood",
            executor.submit(get_contamination_sites, lon, lat): "contamination",
            executor.submit(get_elevation, lon, lat): "elevation",
            executor.submit(get_sea_level_rise, lon, lat): "sea_level_rise",
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"error": str(e)}

    # Clean up BFE sentinel values (-9999 means N/A in FEMA data)
    bfe = results.get("flood", {}).get("base_flood_elevation")
    if bfe is not None and bfe <= -9999:
        results["flood"]["base_flood_elevation"] = None
        bfe = None

    # Compute freeboard (elevation minus base flood elevation)
    elevation_ft = results.get("elevation", {}).get("elevation_ft")

    freeboard = None
    freeboard_status = None
    if elevation_ft is not None and bfe is not None:
        freeboard = round(elevation_ft - bfe, 1)
        freeboard_status = "above" if freeboard >= 0 else "below"

    return {
        "address": address,
        "coordinates": {"lon": lon, "lat": lat},
        "flood": results.get("flood", {}),
        "contamination": results.get("contamination", {}),
        "elevation": results.get("elevation", {}),
        "sea_level_rise": results.get("sea_level_rise", {}),
        "freeboard": {
            "value_ft": freeboard,
            "status": freeboard_status,
        },
    }
