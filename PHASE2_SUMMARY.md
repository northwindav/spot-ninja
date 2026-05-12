# Phase 2 Summary: WindNinja Container Configuration

## ✅ Deliverables

### 1. Dockerfile (`docker/Dockerfile`)
- 160+ lines, fully commented
- Ubuntu 20.04 base (official WindNinja standard)
- CMake flags pre-configured for Spot-Ninja MVP:
  - NINJAFOAM=ON (momentum solver)
  - NINJA_GUI=OFF (CLI-only, ~1-2hr faster build)
  - BUILD_FETCH_DEM=ON
  - BUILD_SLOPE_ASPECT_GRID=ON
  - BUILD_FLOW_SEPARATION_GRID=ON
- Entrypoint: `/data` volume mount for data exchange
- Environment variables for runtime config (CPL_DEBUG, SRTM_API_KEY, etc.)

### 2. Build Automation
- **Windows**: `docker/build_docker.bat` — Batch script with git clone + build
- **Linux/Mac**: `docker/build_docker.sh` — Bash script with same flow
- Both handle:
  - Cloning WindNinja source (if not present)
  - Building image with tagged name
  - Post-build verification instructions

### 3. Documentation
- **PHASE2.md** — Detailed build & run instructions, troubleshooting, size expectations
- Updated **docker/README.md** — Quick reference with examples
- Build commands for all platforms (Windows batch, Linux bash, manual Docker CLI)

## 🚀 Next Steps: Run the Build

### Option A: Windows (PowerShell/Command Prompt)
```powershell
cd .\docker
.\build_docker.bat --tag windninja:latest
```
⏱️ Expected time: 30-45 minutes (depends on CPU cores, network speed)

### Option B: Linux/Mac (Terminal)
```bash
cd ./docker
bash ./build_docker.sh --tag windninja:latest
```

### Option C: Manual (All Platforms)
```bash
# Clone WindNinja source
git clone https://github.com/firelab/windninja.git windninja_source

# Build image
docker build -t windninja:latest -f docker/Dockerfile windninja_source/
```

## ✅ Verification (After Build)

```bash
# Check image
docker images | grep windninja

# Verify binary
docker run --rm windninja:latest windninja --help
# Expected output: "Usage: windninja [options] dem_file ..."

# Test with data (Phase 3+)
docker run -v $(pwd)/data:/data windninja:latest windninja /data/config.sta
```

## 📋 Architecture

```
Host (Windows 11)
├─ DEM Retriever (Python) → /data/dems/
├─ Weather Retriever (Python) → /data/weather/
├─ Config Generator (Python) → /data/config.sta
└─ Docker Run Command
   └─ Container (Ubuntu 20.04)
      ├─ WindNinja binary
      ├─ OpenFOAM 8
      └─ Output → /data/output/ (KMZ)
```

## 🔧 Key Build Parameters

| Parameter | Value | Note |
|-----------|-------|------|
| Base Image | `ubuntu:20.04` | Official WindNinja standard |
| Parallel Build | `make -j12` | Adjust in Dockerfile if CPU < 12 cores |
| Expected Size | 3-4 GB | Full build + deps + OpenFOAM |
| Build Time | 30-45 min | Depends on network/CPU |
| CLI Only | Yes | No Qt 4.8.5 GUI dependency |

## 📚 References

- **Dockerfile**: [docker/Dockerfile](./Dockerfile) (160 lines, well-commented)
- **Build Guide**: [docker/PHASE2.md](./PHASE2.md) (detailed troubleshooting)
- **Official WindNinja**: https://github.com/firelab/windninja
- **Build Source**: https://github.com/firelab/windninja/blob/master/Dockerfile

## 🛠️ Environment Variables (Runtime)

Set via `-e` flag when running container:
```bash
-e CPL_DEBUG=NINJAFOAM        # OpenFOAM momentum solver debug
-e CPL_DEBUG=STABILITY        # Atmospheric stability model debug
-e CPL_DEBUG=GTIFF            # GeoTIFF output debug
-e CUSTOM_SRTM_API_KEY=...    # For auto-DEM download (optional)
```

---

## Status

✅ **Phase 2 (Build Container)**: COMPLETE
- Dockerfile ready
- Build scripts ready
- Documentation complete

⏭️ **Phase 3 (Data Retrieval)**: NOT STARTED
- DEM retriever (CanElevation AWS S3)
- Weather retriever (MSC GeoMet)
- Data validation

---

**Ready to build the container, or shall we wait?** 
(Build takes 30-45 min; good time for a break/coffee ☕)
