# Ground Truth MDC — Project Context

## What Is This
Property risk assessment tool for Miami-Dade County.
Enter an address, get flood zone, contamination proximity,
elevation, and sea level rise vulnerability in plain English.

## Owner
Diego Abreu — PM for Miami-Dade County Commissioner, runs Abreu Data Works LLC.

## Tech Stack
Flask, Leaflet.js, Anthropic Claude API, ArcGIS REST APIs (no auth needed)

## Data Sources
- FEMA Flood Zone: Miami-Dade GIS / FEMA NFHL
- Contamination: Florida DEP ERIC database (ca.dep.state.fl.us)
- Elevation: USGS National Map
- Sea Level Rise: NOAA coastal services

## Related Projects
- miami21-translator (zoning code lookup — same address input pattern)
- Links to: "View zoning for this address →"

## Build Rules
- Keep dependencies minimal
- All API calls are to free public endpoints, no auth needed except Anthropic
- Cache results where possible (flood zones don't change often)
- Aggregate contamination data — never expose individual names/PII
- Include data disclaimers (not financial advice, not survey-grade, etc.)
