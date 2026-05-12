# Docker Configuration for WindNinja

## Overview
This directory contains Docker configuration for building and running WindNinja in a containerized environment.

## Build Strategy

### Dockerfile ✅ (Phase 2 Complete)
- Based on WindNinja's official Dockerfile (Ubuntu 20.04)
- CMake flags configured:
  - `NINJAFOAM=ON` (momentum solver)
  - `NINJA_GUI=OFF` (CLI only; faster build)
  - `BUILD_FETCH_DEM=ON` (DEM download capability)
  - `BUILD_SLOPE_ASPECT_GRID=ON`
  - `BUILD_FLOW_SEPARATION_GRID=ON`
- Target: CLI-only for MVP; GUI optional in Phase 2+

### Build Commands
**Windows (PowerShell):**
```powershell
cd .\docker
.\build_docker.bat --tag windninja:latest
```

**Linux/Mac (Bash):**
```bash
cd ./docker
bash ./build_docker.sh --tag windninja:latest
```

### Run Commands
```bash
# Verify build
docker run --rm windninja:latest windninja --help

# Run with config
docker run -v $(pwd)/data:/data windninja:latest windninja /data/config.sta

# With debugging
docker run -e CPL_DEBUG=NINJAFOAM -v $(pwd)/data:/data windninja:latest windninja /data/config.sta
```

For detailed build instructions, see [PHASE2.md](./PHASE2.md)

## Data Exchange
- Host → Container: Input DEM, weather data via `/data/` volume mount
- Container → Host: Output KMZ files via same volume
- No authentication required for CanElevation S3 access

## Troubleshooting
- Verify Docker Desktop is running (no admin rights required for non-Hyper-V setups)
- Check volume mount permissions if data access fails
- Review container logs: `docker logs <container_id>`

## Future: Singularity Alternative
- Conversion path documented for HPC environments
- See: https://github.com/firelab/windninja/wiki/Building-WindNinja-with-Docker-and-Using-it-in-a-HPC-Environment
