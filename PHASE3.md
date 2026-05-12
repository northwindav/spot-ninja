# Phase 3: Data Retrieval Integration

## Overview

Phase 3 implements the critical data pipeline: fetching Canadian DEM and weather data, validating inputs, and preparing everything for WindNinja simulation.

---

## Modules Implemented

### 1. **validators.py** — Input Validation
- Validates latitude/longitude (Canada bounds, HRDPS domain)
- Validates ROI size (2-50 km)
- Validates DEM collections (CanElevation options)
- Validates weather models (HRDPS/GDPS, resolutions)
- Comprehensive `validate_all()` for full parameter checking

**Key Functions:**
```python
validate_coordinates(latitude, longitude, strict=True)
validate_roi_size(roi_km)
validate_dem_collection(collection)
validate_weather_model(model, resolution)
validate_all(latitude, longitude, roi_km, dem_collection, model, resolution)
```

### 2. **dem_retriever.py** — DEM Download (CanElevation AWS S3)

**Features:**
- Access CanElevation S3 buckets (no auth required)
- Collection cascade: HRDEM 1m → 2m → MRDEM 30m
- Bounding box calculation (accounts for lat/lon degree variance)
- S3 tile listing and download
- DEM validation (dimensions, CRS, data integrity)

**Key Class:**
```python
retriever = DEMRetriever(output_dir="data/dems")
dem_path = retriever.download_dem(
    latitude=51.0, 
    longitude=-114.0, 
    roi_km=10.0,
    collection="hrdem-mosaic-1m",
    cascade=True
)
if retriever.validate_dem(dem_path):
    print("✓ DEM ready")
```

**Collections Supported:**
- `hrdem-mosaic-1m` — 1m LiDAR+optical (preferred)
- `hrdem-mosaic-2m` — 2m LiDAR+optical
- `mrdem-30` — 30m Copernicus+LiDAR (complete coverage)
- `hrdem-lidar` — Project-based LiDAR
- `hrdem-arcticdem` — Arctic 2m

### 3. **weather_retriever.py** — Weather Data (MSC GeoMet API)

**Features:**
- Query MSC GeoMet API (no auth required)
- Supports HRDPS (1.0km, 2.5km) and GDPS (10km)
- Automatic latest forecast detection
- Point-based queries (lat/lon)
- Metadata caching (JSON)
- Forecast validation

**Key Class:**
```python
retriever = WeatherRetriever(output_dir="data/weather")
forecast_path = retriever.download_forecast(
    model="HRDPS",
    resolution="2.5km",
    latitude=51.0,
    longitude=-114.0,
    forecast_hours=(12, 36)
)
if retriever.validate_forecast(forecast_path):
    print("✓ Forecast ready")
```

**Models:**
- HRDPS 1.0km (high-res, limited areas)
- HRDPS 2.5km (continental Canada) ← recommended
- GDPS 10km (global fallback)

### 4. **utils.py** — Utilities & Configuration

**Features:**
- Logging setup (console + optional file)
- .env file loading
- YAML config parsing
- Data path management
- Config class with dot-notation access

**Key Functions:**
```python
setup_logging(log_level="INFO", log_file=Path("spot-ninja.log"))
load_env_file(Path(".env"))
config = Config(Path("config/spot-ninja.yaml"))
latitude = config.get("location.latitude")
stability_enabled = config.stability_enabled()
```

### 5. **spot_ninja.py** — Main Orchestration (MVP)

**Usage:**
```bash
python spot_ninja.py \
  --lat 51.0 \
  --lon -114.0 \
  --config config/spot-ninja.yaml \
  --data-dir data \
  --log-level INFO
```

**Workflow:**
1. Parse CLI arguments
2. Load config + environment
3. Validate all inputs
4. Download DEM (with cascade fallback)
5. Download weather data
6. Output readiness check

**Options:**
- `--skip-dem` — Skip DEM download (for testing)
- `--skip-weather` — Skip weather download
- `--log-level` — DEBUG, INFO, WARNING, ERROR

---

## Installation & Setup

### 1. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env if needed (SRTM API key optional)

cp config/spot-ninja.yaml.example config/spot-ninja.yaml
# Edit config/spot-ninja.yaml for your location
```

### 4. Run Orchestration Script
```bash
python scripts/spot_ninja.py \
  --lat 51.0 \
  --lon -114.0 \
  --config config/spot-ninja.yaml
```

---

## Testing

### Test Validator
```python
from validators import validate_all

result = validate_all(
    latitude=51.0,
    longitude=-114.0,
    roi_km=10.0,
    dem_collection="hrdem-mosaic-1m",
    model="HRDPS",
    resolution="2.5km"
)
print(f"Valid: {result['valid']}")
print(f"Errors: {result['errors']}")
print(f"Warnings: {result['warnings']}")
```

### Test DEM Retriever
```bash
cd scripts
python -c "from dem_retriever import demo; demo()"
# Downloads sample DEM for Alberta Foothills
```

### Test Weather Retriever
```bash
cd scripts
python -c "from weather_retriever import demo; demo()"
# Queries sample HRDPS forecast
```

### Test Main Script
```bash
python scripts/spot_ninja.py \
  --lat 51.0 \
  --lon -114.0 \
  --data-dir data \
  --log-level DEBUG
```

---

## Test Locations (4 Terrain Types)

### 1. Flat (Prairies)
```bash
python scripts/spot_ninja.py --lat 49.0 --lon -105.0  # Saskatchewan
```

### 2. Rolling (Foothills)
```bash
python scripts/spot_ninja.py --lat 51.0 --lon -114.0  # Alberta
```

### 3. Mountainous (Interior)
```bash
python scripts/spot_ninja.py --lat 55.0 --lon -120.0  # BC Interior
```

### 4. Extreme (Coastal Mountains)
```bash
python scripts/spot_ninja.py --lat 49.0 --lon -125.0  # BC Coast
```

---

## Dependencies

**Core:**
- `boto3` — AWS S3 access (CanElevation)
- `requests` — HTTP API calls (GeoMet)
- `pyyaml` — Config parsing
- `python-dotenv` — .env file loading

**Geospatial:**
- `gdal` — Geospatial data (may require system installation)
- `rasterio` — GeoTIFF reading/writing
- `shapely` — Geometry operations
- `pyproj` — Coordinate transformations
- `xarray` — NetCDF handling
- `netCDF4` — NetCDF support

**See:** `requirements.txt`

---

## Known Limitations (MVP)

1. **Single-tile DEM**: Downloads first tile only; production would mosaic multiple tiles
2. **Forecast metadata only**: Weather retriever saves JSON metadata; production needs actual NetCDF/GeoTIFF files
3. **No data format conversion**: Raw outputs; Phase 4 adds config generation + format conversion
4. **No batch processing**: Single run per invocation; Phase 5+ adds batch mode
5. **Limited error handling**: Basic fallbacks; production needs more robust retry logic

---

## Next: Phase 4 (Host Orchestration)

Once Phase 3 data is ready:
1. Generate WindNinja `.sta` config file
2. Invoke Docker container with `/data` mount
3. Monitor container execution
4. Retrieve + validate output (KMZ, logs)

---

## References

- **CanElevation**: https://registry.opendata.aws/canelevation-dem/
- **MSC GeoMet**: https://api.weather.gc.ca/
- **STAC Catalog**: https://datacube.services.geo.ca/stac/api/
- **Rasterio Docs**: https://rasterio.readthedocs.io/
- **Requests Docs**: https://requests.readthedocs.io/
