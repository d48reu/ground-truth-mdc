import os
import anthropic

SYSTEM_PROMPT = """You are a plain-English property risk advisor for Miami-Dade County.
Given the following data about a property, write a 3-4 sentence summary
that a homebuyer with no technical knowledge would understand.
Be direct and factual. Don't sugarcoat risks. Don't give financial advice.
Explain what the flood zone means for insurance, what the contamination
proximity means for health/environment, and what sea level rise means
for long-term property viability."""


def build_user_prompt(profile):
    """Build the user prompt from a risk profile dict."""
    flood = profile.get("flood", {})
    elevation = profile.get("elevation", {})
    contamination = profile.get("contamination", {})
    slr = profile.get("sea_level_rise", {})
    fb = profile.get("freeboard", {})

    elevation_ft = elevation.get("elevation_ft", "Unknown")
    bfe = flood.get("base_flood_elevation", "N/A")
    freeboard_val = fb.get("value_ft")
    freeboard_str = f"{freeboard_val} ft ({fb.get('status', '')} BFE)" if freeboard_val is not None else "N/A"

    # Contamination summary
    contam_count = contamination.get("total_count", 0)
    by_program = contamination.get("by_program", {})
    site_types = ", ".join(f"{v} {k}" for k, v in by_program.items()) if by_program else "None"
    nearest = contamination.get("nearest")
    nearest_str = "None within 1 mile"
    if nearest:
        nearest_str = (
            f"{nearest.get('name', 'Unknown')} "
            f"({nearest.get('distance_ft', '?')} ft away, "
            f"status: {nearest.get('site_status', nearest.get('status', 'Unknown'))})"
        )

    return f"""Property at {profile.get('address', 'Unknown address')}
- FEMA Flood Zone: {flood.get('zone', 'Unknown')} ({flood.get('risk_level', 'Unknown')})
  Base Flood Elevation: {bfe} ft
- Property Elevation: {elevation_ft} ft above sea level
- Freeboard: {freeboard_str}
- Sea Level Rise: Property inundated at {slr.get('first_inundation_ft', 'N/A')}ft rise (projected {slr.get('projected_year', 'N/A')})
- Contamination sites within 1 mile: {contam_count}
  Types: {site_types}
  Nearest: {nearest_str}"""


def get_risk_summary(profile):
    """Call Anthropic API to generate plain English risk summary."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI summary unavailable — ANTHROPIC_API_KEY not configured."

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = build_user_prompt(profile)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text
    except Exception as e:
        return f"AI summary unavailable: {e}"
