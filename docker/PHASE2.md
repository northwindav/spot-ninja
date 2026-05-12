# Phase 2: Build WindNinja Container

## Overview

This phase builds a Docker container with WindNinja compiled according to Spot-Ninja MVP specifications.

### Dockerfile Location
[Dockerfile](./Dockerfile) - Customized from official WindNinja Dockerfile (Ubuntu 20.04)

### Build Configuration

#### CMake Flags (Spot-Ninja MVP)
- `NINJAFOAM=ON` — Momentum solver (required for wind simulation)
- `NINJA_GUI=OFF` — CLI only (faster build, no Qt 4.8.5 dependency)
- `BUILD_FETCH_DEM=ON` — Auto-download DEM capability
- `BUILD_SLOPE_ASPECT_GRID=ON` — Terrain analysis
- `BUILD_FLOW_SEPARATION_GRID=ON` — Wind flow separation modeling
- `SUPRESS_WARNINGS=ON` — Cleaner build output

#### Base Image
- Ubuntu 20.04 (official WindNinja base)
- All dependencies installed via `build_deps_docker.sh`

#### Working Directory
- `/data` — Mounted from host for input/output file exchange

### Build Instructions

#### Option A: Windows (PowerShell)
```powershell
cd .\docker
.\build_docker.bat --tag windninja:latest
```

#### Option B: Linux/Mac (Bash)
```bash
cd ./docker
bash ./build_docker.sh --tag windninja:latest
```

#### Option C: Manual Docker Build
```bash
# Requires WindNinja source cloned to windninja_source/
git clone https://github.com/firelab/windninja.git windninja_source

# Build
docker build -t windninja:latest -f docker/Dockerfile windninja_source/
```

### Verify Build

```bash
# Check image exists
docker images | grep windninja

# Verify binary
docker run --rm windninja:latest windninja --help

# Output: Usage: windninja [options] dem_file
#         Options:
#           ...
```

### Run Container

#### Basic Run (with config file)
```bash
docker run -v $(pwd)/data:/data windninja:latest windninja /data/config.sta
```

#### With Debugging
```bash
# OpenFOAM debugging
docker run -e CPL_DEBUG=NINJAFOAM -v $(pwd)/data:/data windninja:latest windninja /data/config.sta

# Stability model debugging
docker run -e CPL_DEBUG=STABILITY -v $(pwd)/data:/data windninja:latest windninja /data/config.sta

# GeoTIFF output debugging
docker run -e CPL_DEBUG=GTIFF -v $(pwd)/data:/data windninja:latest windninja /data/config.sta
```

#### Interactive Shell (for troubleshooting)
```bash
docker run -it -v $(pwd)/data:/data windninja:latest /bin/bash
# Inside container:
windninja /data/config.sta
```

### Data Exchange

The container expects input and output files via the `/data` volume:

```
./data/
├── dems/          → Input elevation models (GeoTIFF)
├── weather/       → Input weather data (NetCDF/GeoTIFF)
└── output/        → Output KMZ/logs (from container)
```

### Build Troubleshooting

#### Build Takes Too Long
- Default: `make -j12` (12 parallel jobs)
- Adjust in Dockerfile if your system has fewer cores
- Or use: `docker build --build-arg JOBS=4 ...`

#### Out of Disk Space
- Docker build can require 10-15 GB
- Clean dangling images: `docker image prune`

#### Permission Denied on Linux
- Run Docker with sudo or add user to docker group:
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```

### Image Size
Expected size: ~3-4 GB (Ubuntu base + full build dependencies + OpenFOAM)

To reduce size in future versions:
- Use multi-stage build to discard build artifacts
- Switch to Ubuntu slim or Alpine base (may require dependency adjustments)

### Singularity Conversion (Phase 6+)

Convert Docker image to Singularity for HPC environments:
```bash
docker build -t windninja:latest -f docker/Dockerfile windninja_source/
singularity build windninja_latest.sif docker-daemon://windninja:latest
```

Reference: https://github.com/firelab/windninja/wiki/Building-WindNinja-with-Docker-and-Using-it-in-a-HPC-Environment

---

## Next: Phase 3 (Data Retrieval Integration)

Once verified, proceed to implement:
- DEM retrieval from CanElevation AWS S3
- Weather data retrieval from MSC GeoMet
- Data validation & preprocessing
