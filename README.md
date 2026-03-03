# Ground Truth MDC

Property climate risk assessment tool for Miami-Dade County. Enter an address, get flood zone, contamination proximity, elevation, and sea level rise vulnerability — explained in plain English.

## What It Does

- Interactive Leaflet.js map of Miami-Dade County
- Address search with geocoding
- Aggregates data from FEMA, Florida DEP, USGS, and NOAA
- Claude AI generates plain-English risk summaries
- All data from free public APIs — no special access required

## Tech Stack

- **Backend:** Flask, Anthropic Claude API
- **Frontend:** Leaflet.js, vanilla HTML/CSS/JS
- **Data Sources:** Miami-Dade GIS, FEMA NFHL, Florida DEP ERIC, USGS, NOAA

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env  # Add your ANTHROPIC_API_KEY
python app.py
```

## Environment Variables

- `ANTHROPIC_API_KEY` — Required for AI risk summaries

## Deployment

Configured for Render.com via `render.yaml`.

## License

All rights reserved. Abreu Data Works LLC.
