# Scripts Directory

## Phase 3: Data Retrieval Modules ✅ (COMPLETE)

### Core Modules

#### `spot_ninja.py` — Main Orchestration (MVP)
Entry point for single-run automation.

**Usage:**
```bash
python spot_ninja.py --lat 51.0 --lon -114.0 --config config/spot-ninja.yaml
```

**Workflow:**
1. Parse inputs + load config
2. Validate all parameters
3. Download DEM (CanElevation)
4. Download weather data (MSC GeoMet)
5. Output readiness report

**Options:**
- `--skip-dem`, `--skip-weather` — Skip components for testing
- `--log-level DEBUG|INFO|WARNING|ERROR` — Logging verbosity

#### `dem_retriever.py` — DEM Download (CanElevation AWS S3)
Downloads high-resolution Canadian elevation models.

**Class:** `DEMRetriever`
- Automatic collection cascade (1m → 2m → 30m)
- Bounding box from lat/lon + ROI size
- S3 tile discovery + download
- GeoTIFF validation

**Collections:**
- `hrdem-mosaic-1m` (preferred)
- `hrdem-mosaic-2m`
- `mrdem-30` (complete nationwide)
- `hrdem-lidar`, `hrdem-arcticdem`

**Example:**
```python
retriever = DEMRetriever(Path("data/dems"))
dem_path = retriever.download_dem(51.0, -114.0, 10.0)
```

#### `weather_retriever.py` — Weather Data (MSC GeoMet API)
Downloads weather forecasts for initialization.

**Class:** `WeatherRetriever`
- HRDPS 1.0km, 2.5km (Canada)
- GDPS 10km (global fallback)
- Point-based queries
- Automatic latest forecast detection
- JSON metadata caching

**Example:**
```python
retriever = WeatherRetriever(Path("data/weather"))
forecast_path = retriever.download_forecast("HRDPS", "2.5km", 51.0, -114.0)
```

#### `validators.py` — Input Validation
Comprehensive parameter validation.

**Functions:**
- `validate_coordinates()` — Lat/lon bounds checking
- `validate_roi_size()` — Region size validation
- `validate_dem_collection()` — DEM options
- `validate_weather_model()` — Model/resolution pairs
- `validate_all()` — Full parameter set validation

**Example:**
```python
from validators import validate_all
result = validate_all(51.0, -114.0, 10.0, "hrdem-mosaic-1m", "HRDPS", "2.5km")
if result["valid"]:
    print("✓ All inputs valid")
```

#### `utils.py` — Utilities & Configuration
Common functions, logging, config management.

**Classes & Functions:**
- `setup_logging()` — Initialize logging
- `load_env_file()` — Load .env variables
- `load_config()` — Parse YAML config
- `Config` class — Config object with dot-notation access
- `get_data_paths()` — Standard directory paths

**Example:**
```python
from utils import Config
config = Config(Path("config/spot-ninja.yaml"))
latitude = config.get("location.latitude")
stability = config.stability_enabled()
```

---

## Dependencies

**Install all:**
```bash
pip install -r requirements.txt
```

**Key packages:**
- `boto3` — AWS S3 (CanElevation)
- `requests` — HTTP (GeoMet API)
- `rasterio` — GeoTIFF (DEM validation)
- `xarray`, `netCDF4` — NetCDF handling
- `PyYAML` — Config parsing
- `python-dotenv` — .env loading

---

## Setup & Execution

### 1. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
cp config/spot-ninja.yaml.example config/spot-ninja.yaml
# Edit as needed
```

### 4. Run
```bash
python spot_ninja.py --lat 51.0 --lon -114.0 --config config/spot-ninja.yaml
```

---

## Testing

### Test Single Module
```bash
# DEM retriever
python -c "from dem_retriever import demo; demo()"

# Weather retriever
python -c "from weather_retriever import demo; demo()"

# Validators
python -c "from validators import validate_all; print(validate_all(51, -114, 10, 'hrdem-mosaic-1m', 'HRDPS', '2.5km'))"
```

### Test 4 Terrain Types
```bash
# Flat (prairie)
python spot_ninja.py --lat 49 --lon -105

# Rolling (foothills)
python spot_ninja.py --lat 51 --lon -114

# Mountainous (interior)
python spot_ninja.py --lat 55 --lon -120

# Extreme/Coastal
python spot_ninja.py --lat 49 --lon -125
```

---

## Future Modules (Phase 4+)

- `config_generator.py` — Generate WindNinja `.sta` config files
- `container_runner.py` — Invoke Docker container with data mounts
- `output_processor.py` — Post-process WindNinja output (KMZ validation, etc.)
- `test_*.py` — Unit tests for each module
- `test_integration.py` — End-to-end integration tests

---

## Documentation

- [PHASE3.md](../PHASE3.md) — Phase 3 detailed guide
- [README.md](../README.md) — Project overview
- [SETUP.md](../SETUP.md) — Setup instructions
