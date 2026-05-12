# Scripts Directory

## Planned Structure (Phase 2+)

### Core Orchestration
- `spot_ninja.py` — Main CLI entry point
  - Usage: `python spot_ninja.py --lat XX --lon YY --config spot-ninja.yaml`
  - Handles: data retrieval, config generation, Docker invocation

### Data Retrieval Modules
- `dem_retriever.py` — CanElevation AWS S3 DEM download & processing
- `weather_retriever.py` — MSC GeoMet HRDPS/GDPS retrieval & conversion

### Utilities
- `validators.py` — Input validation (lat/lon within domain, etc.)
- `config_generator.py` — Auto-generate WindNinja config from YAML template
- `output_processor.py` — Post-process WindNinja output

### Testing
- `test_*.py` — Unit tests for each module
- `test_integration.py` — End-to-end integration tests (4 terrain types)

## Requirements
- Python 3.11+
- Dependencies: GDAL, boto3 (AWS S3), pyyaml, requests
- See: `requirements.txt` (TBD - Phase 2)

## Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```
