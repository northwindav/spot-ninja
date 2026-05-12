# Spot-Ninja Project Structure

## Directories

```
spot-ninja/
├── README.md                    # This file
├── spot-ninja.code-workspace    # VS Code workspace
├── .gitignore                   # Git exclusions
├── .env.example                 # API credential template
│
├── data/                        # Data exchange directory (host ↔ container)
│   ├── dems/                    # Downloaded DEMs (GeoTIFF)
│   ├── weather/                 # Downloaded weather data (NetCDF/GeoTIFF)
│   └── output/                  # WindNinja output (KMZ, logs)
│
├── config/                      # Configuration templates
│   └── spot-ninja.yaml.example  # YAML config template
│
├── scripts/                     # Python orchestration (TBD - Phase 2)
│   └── README.md                # Script module descriptions
│
└── docker/                      # Container configuration (TBD - Phase 2)
    └── README.md                # Docker build & run instructions
```

## Setup Instructions

### Prerequisites
- Windows 11 (or WSL2)
- Docker Desktop (free, community edition)
- Python 3.11 or higher
- Git (for version control)

### 1. Clone / Setup Repository
```bash
cd c:\Users\michsmit\OneDrive - NRCan RNCan\Documents\projects\forecast-products\spot-ninja
```

### 2. Copy Configuration Templates
```bash
# Create .env from template
cp .env.example .env
# Edit .env and fill in any required API credentials (see comments)

# Create config from template
cp config/spot-ninja.yaml.example config/spot-ninja.yaml
# Edit config/spot-ninja.yaml for your test case
```

### 3. Python Virtual Environment (Phase 2+)
```bash
# Create venv
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies (TBD - Phase 2)
# pip install -r requirements.txt
```

### 4. Docker Setup (Phase 2+) - GitHub Actions
See [GITHUB_ACTIONS.md](./GITHUB_ACTIONS.md) for detailed instructions.

**Summary:**
```bash
# 1. Push repository to GitHub
git push -u origin main

# 2. Trigger build in GitHub Actions (Actions → Run workflow)
# 3. Wait 30-45 minutes for build
# 4. Download windninja-docker-image.tar artifact

# 5. Load image locally
docker load -i windninja-image.tar

# 6. Verify build
docker run --rm windninja:latest windninja --help
```

### 5. Run Spot-Ninja (Phase 3+)
```bash
# Activate venv
venv\Scripts\activate

# Single run
python scripts/spot_ninja.py --lat 51.0 --lon -114.0 --config config/spot-ninja.yaml

# Output will be in data/output/
```

## Development Phases

### Phase 1: Environment & Container Setup ✓ (IN PROGRESS)
- [x] Folder structure
- [x] Configuration templates
- [ ] Docker setup verification

### Phase 2: Build WindNinja Container ✅ (COMPLETE)
- [x] Customize Dockerfile with MVP flags
- [x] Create build scripts (Windows batch + Linux bash)
- [x] Set up GitHub Actions cloud build (no Docker Desktop needed!)
- [x] Document build process and debugging options
- [ ] Trigger build in GitHub Actions and download artifact (next step)

**Note**: Using GitHub Actions cloud build instead of local Docker due to virtualization constraints. See [GITHUB_ACTIONS.md](./GITHUB_ACTIONS.md)

### Phase 3: Data Retrieval Integration
- [ ] DEM retriever (CanElevation AWS S3)
- [ ] Weather retriever (MSC GeoMet)
- [ ] Data validation & preprocessing

### Phase 4: Host Orchestration
- [ ] Python CLI (`spot_ninja.py`)
- [ ] Config file generation
- [ ] Docker container invocation

### Phase 5: Testing & Validation
- [ ] 4-terrain test cases
- [ ] End-to-end validation
- [ ] Output verification (KMZ inspection)

### Phase 6: Documentation & Deployment
- [ ] User guide
- [ ] Troubleshooting
- [ ] Singularity alternative (optional)

## Key Design Decisions

| Item | Decision |
|------|----------|
| Container Technology | Docker (Option A) |
| DEM Source | CanElevation AWS (1m → 2m → 30m) |
| Weather Models | HRDPS 1.0km → 2.5km → GDPS |
| Config Format | YAML |
| Python Version | 3.11+ |
| Output Format (MVP) | KMZ |
| ROI Size | ~10 km × 10 km |
| Build Sequence | Sequential phases |
| Orchestration | Host-based Python script |

## API Credentials

### CanElevation (NRCan via AWS)
- **Access**: Public S3 buckets (no authentication)
- **URL**: `s3://canelevation-dem/hrdem-mosaic-1m/`
- **STAC**: https://datacube.services.geo.ca/stac/api/

### MSC GeoMet
- **Access**: Free (no API key needed for basic access)
- **URL**: https://api.weather.gc.ca/
- **Documentation**: https://eccc-msc.github.io/open-data/msc-geomet/readme_en/

### OpenTopography SRTM (optional, for fallback)
- **Access**: Requires free API key
- **URL**: https://opentopography.org/
- **Setup**: Get key from portal, add to `.env` as `CUSTOM_SRTM_API_KEY`

## Testing Terrain Types (Phase 5)

1. **Flat**: Prairie (e.g., Saskatchewan, ~49°N 105°W)
2. **Rolling**: Foothills (e.g., Alberta, ~51°N 114°W)
3. **Mountainous**: Interior BC (e.g., ~55°N 120°W)
4. **Extreme/Coastal**: BC Coast (e.g., ~49°N 125°W)

## Troubleshooting

### Docker Issues
- Ensure Docker Desktop is running
- Check: `docker --version`
- No admin rights needed for community edition on Windows 11

### Data Access
- Verify AWS CLI installed: `aws --version`
- Test S3 access: `aws s3 ls --no-sign-request s3://canelevation-dem/`

### Python Issues
- Verify version: `python --version` (should be 3.11+)
- Activate venv before running scripts

## References

- **WindNinja**: https://github.com/firelab/windninja
- **CanElevation**: https://registry.opendata.aws/canelevation-dem/
- **MSC GeoMet**: https://www.canada.ca/en/environment-climate-change/services/weather.html
- **Project README**: [Original project scope](./README.md)

---

**Last Updated**: May 10, 2026  
**Phase**: 1 (Environment Setup)
