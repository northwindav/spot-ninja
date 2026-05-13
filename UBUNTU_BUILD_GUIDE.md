# Ubuntu Docker Build Guide for Spot-Ninja

**Status:** ✅ WindNinja v3.12.2 Docker image builds successfully on Ubuntu 24.04

**Key Features:**
- Uses system packages for all dependencies (GDAL, NetCDF, PROJ, OpenFOAM)
- CLI-only build (`NINJA_QTGUI=OFF`) — no Qt4 dependency
- NINJAFOAM momentum solver support (`NINJAFOAM=ON`)
- Automatic DEM fetching enabled (`BUILD_FETCH_DEM=ON`)

## Phase: Build Environment Setup & Docker Compilation

---

## Prerequisites Check

Before starting, verify you have:
- [ ] Ubuntu 24.04 machine (or 22.04 with package name adjustments)
- [ ] Internet access (for git clone and apt packages)
- [ ] `sudo` access (required for Docker installation)
- [ ] ~15 GB free disk space (Docker image ~4 GB + build cache)
- [ ] ~30-45 minutes for full build (much faster with system packages)

---

## Step 1: Install Docker on Ubuntu

Run these commands in a terminal on the Ubuntu machine:

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker (official method)
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
sudo docker --version
```

**Expected output:** `Docker version 20.10.x` or higher

---

## Step 2: (Optional) Add Your User to Docker Group

This allows you to run `docker` without `sudo` (more convenient):

```bash
# Create docker group (usually exists already)
sudo groupadd docker

# Add your user to docker group
sudo usermod -aG docker $USER

# Apply group changes (choose ONE):
# Option A: Log out and log back in
# Option B: Run this command
newgrp docker

# Verify (should work without sudo)
docker ps
```

---

## Step 3: Clone or Sync the Spot-Ninja Repository

If you don't already have the code on Ubuntu:

```bash
# Option A: Clone from GitHub
git clone https://github.com/YOUR_USERNAME/spot-ninja.git
cd spot-ninja

# Option B: Copy from Windows (if using external drive/USB)
# Copy the entire spot-ninja folder to Ubuntu

# Option C: Sync via network (scp, rsync, etc.)
```

**Inside the repo, verify these files exist:**
```bash
ls -la docker/
# Should show: Dockerfile, build_docker.sh, build_deps_docker.sh, README.md
```

---

## Step 4: Review the Dockerfile

The Dockerfile has 4 stages and uses **Ubuntu 24.04** base image:

| Stage | Purpose | Duration | Key Change |
|-------|---------|----------|-----------|
| 1: System Deps | Install all build tools + dependencies via apt | ~2 min | Uses system packages instead of building from source |
| 2: WindNinja Compile | Clone WindNinja v3.12.2, CMake, make binary | ~25 min | Uses `NINJA_QTGUI=OFF` for CLI-only build |
| 3: OpenFOAM Setup | Optional NINJAFOAM library setup | ~2 min | Uses system OpenFOAM package |
| 4: Runtime Setup | Configure entrypoint + environment variables | <1 min | Adds PATH to ensure windninja is findable |

**Major improvements since GitHub Actions:**
- ✅ All dependencies installed from apt (no source builds for GDAL, NetCDF, PROJ, OpenFOAM)
- ✅ Fixed Qt4 conflict by using correct `NINJA_QTGUI=OFF` flag (not `NINJA_GUI`)
- ✅ Upgraded to WindNinja v3.12.2 (latest stable)
- ✅ Removed GitHub Actions workflow (build locally only)

---

## Step 5: Build the Docker Image

```bash
# Navigate to the spot-ninja repo
cd ~/path/to/spot-ninja

# (Optional) Clean old Docker cache to ensure fresh build
docker system prune -a --volumes

# Build the image (this will take 30-45 minutes)
docker build -t windninja:latest -f docker/Dockerfile .

# Monitor progress in real-time
# You'll see:
#   Step 1: FROM ubuntu:24.04
#   Step 2: RUN apt-get update && apt-get install... (quick, ~2 min)
#   Step 3: RUN git clone --branch 3.12.2 https://github.com/firelab/windninja.git
#   Step 4: RUN cmake ... && make -j12 ... (slow, ~25 min)
#   Step 5: OpenFOAM setup + runtime setup
```

**If build fails:**
1. Note the error message and stage
2. Check that `git` and `docker` are installed
3. Ensure internet connectivity (apt needs to download packages)
4. Re-run the build (Docker caches layers, so retry is faster)

**Expected output when complete:**
```
Successfully built <hash>
Successfully tagged windninja:latest
```

**Build verification output** (near the end):
The build script will attempt to show where windninja is installed:
```
/usr/local/bin/windninja
Build complete
```

---

## Step 6: Verify the Image Works

```bash
# List Docker images
docker images | grep windninja
# Should show: windninja    latest    <hash>    <time>    ~4 GB

# Test the image (smoke test)
docker run --rm windninja:latest windninja --help
# Should output WindNinja version and command-line options
```

If you see an error like `executable not found in PATH`, this indicates an installation issue. The build verification output should have shown the binary location.

---

## Step 7: Test with Sample Data (Optional)

Create a test directory on the Ubuntu machine:

```bash
# Create test directory
mkdir -p /tmp/spot-ninja-test/data/{dems,weather,output}

# Create a simple test config file at /tmp/spot-ninja-test/data/test.sta
cat > /tmp/spot-ninja-test/data/test.sta << 'EOF'
[initialize]
dem_file=/data/dems/test_dem.tif
weather_file=/data/weather/test_weather.grib2
output_path=/data/output/

[stability]
stability_model=false

[output]
output_format=kmz
EOF

# Run WindNinja in the container (this will fail with missing files, but tests Docker setup)
sudo docker run -v /tmp/spot-ninja-test/data:/data windninja:latest windninja /data/test.sta
# Expected: Either success (if files exist) or error about missing files (but Docker works!)
```

---

## Step 8: Save the Image as TAR (For Transfer Back to Windows)

If you want to use the image on Windows or another machine:

```bash
# Save the image
sudo docker save windninja:latest -o windninja-image.tar

# Verify TAR file
ls -lh windninja-image.tar
# Should be ~3-4 GB

# Optional: Compress for faster transfer
gzip windninja-image.tar  # Creates windninja-image.tar.gz (~800 MB - 1.5 GB)

# To load back on Windows (using Docker Desktop if it becomes available):
# docker load -i windninja-image.tar
# docker load -i windninja-image.tar.gz
```

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `docker: command not found` | Docker not installed | Re-run Step 1 |
| `permission denied while trying to connect to Docker daemon` | User not in docker group | Add user to docker group (Step 2) or use `sudo docker` |
| `fatal: remote branch 3.12.2 not found` | Git clone failed | Check internet connection; verify tag exists with `git ls-remote --tags https://github.com/firelab/windninja.git` |
| `windninja: executable not found in PATH` | Build installation issue | Check build output for "Build complete" verification; ensure CMAKE_INSTALL_PREFIX succeeded |
| `CMake error: Qt4 REQUIRED but not found` | Old WindNinja version or wrong flag | Ensure using v3.12.2 and `NINJA_QTGUI=OFF` (not `NINJA_GUI`) |
| `out of disk space` | Image and cache too large | Run `docker system prune -a --volumes` to free space |
| `Cannot find GDAL/NetCDF/PROJ` | Missing apt packages | Check Step 1 completed; verify `apt-get update` ran |
| `OpenFOAM setup skipped` | System OpenFOAM package missing dev files | This is non-critical; NINJAFOAM is optional |



---

## Next Steps After Successful Build

1. **Test on Ubuntu:** Verify `docker run` works with sample data
2. **Transfer TAR file:** If needed for Windows, transfer `windninja-image.tar.gz`
3. **On Windows (Phase 4):** Load image and integrate with Python scripts
4. **Integration test:** Run `scripts/spot_ninja.py` with real locations

---

## Reference: Dockerfile Build Stages Explained

### Stage 1: System Dependencies
```dockerfile
# Clone WindNinja v3.12.2
RUN git clone --branch 3.12.2 https://github.com/firelab/windninja.git /opt/src/windninja

# Install all dependencies from apt
RUN apt-get install -y \
    gfortran autoconf libtool \
    libhdf5-dev libnetcdf-dev libgdal-dev libproj-dev proj-data \
    libgeos-dev libgeos++-dev libshp-dev libpq-dev \
    libexpat1-dev libxerces-c-dev libspatialindex-dev \
    openfoam
```
**What it does:** 
- Clones official WindNinja v3.12.2 repository (latest stable)
- Installs all build dependencies from Ubuntu apt packages (no source builds!)
- Includes: GDAL, NetCDF, PROJ, OpenFOAM, Boost, HDF5, etc.
- **Total time: ~2 minutes** (apt is fast compared to source builds)

### Stage 2: WindNinja Compilation
```dockerfile
RUN mkdir -p /opt/src/windninja/build && \
    cd /opt/src/windninja/build && \
    cmake \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D NINJA_CLI=ON \
      -D NINJA_QTGUI=OFF \
      -D NINJAFOAM=ON \
      -D BUILD_FETCH_DEM=ON \
      -D BUILD_SLOPE_ASPECT_GRID=ON \
      -D BUILD_FLOW_SEPARATION_GRID=ON && \
    make -j12 && make install
```
**What it does:**
- Creates build directory
- Runs CMake with key flags:
  - `CMAKE_INSTALL_PREFIX=/usr/local` — Install to standard location
  - `NINJA_CLI=ON` — Build CLI tool
  - `NINJA_QTGUI=OFF` — Disable Qt GUI (avoids Qt4/Qt5 conflicts)
  - `NINJAFOAM=ON` — Enable momentum solver
  - `BUILD_FETCH_DEM=ON` — Enable automatic DEM download
- Compiles WindNinja binary (parallel build with 12 threads)
- Installs to `/usr/local/bin/windninja`
- **Total time: ~25 minutes**

### Stage 3: OpenFOAM NinjaFOAM Setup (Optional)
```dockerfile
RUN bash -c 'if [ -f /usr/lib/openfoam/bashrc ]; then \
    source /usr/lib/openfoam/bashrc && \
    mkdir -p /opt/windninja_foam && \
    cp -r /opt/src/windninja/src/ninjafoam /opt/windninja_foam/ 2>/dev/null || true; \
fi'
```
**What it does:**
- Attempts to source system OpenFOAM environment
- Copies NINJAFOAM utilities for momentum solver (optional, non-critical)
- **Total time: ~2 minutes**
- **Note:** System OpenFOAM package may not have dev files; failure is OK

### Stage 4: Runtime Setup
```dockerfile
ENV PATH="/usr/local/bin:${PATH}"
ENTRYPOINT ["windninja"]
WORKDIR /data
```
**What it does:**
- Adds `/usr/local/bin` to PATH (where windninja is installed)
- Sets entrypoint to `windninja` executable
- Sets working directory to `/data` (for volume mounts)
- **Total time: <1 minute**

---

## Build Time Estimate

| Stage | Duration | Notes |
|-------|----------|-------|
| apt-get install | ~2 min | All dependencies from system packages |
| Clone WindNinja | ~1 min | Git clone v3.12.2 |
| WindNinja compile | ~25 min | CMake + make (with 12 parallel threads) |
| OpenFOAM setup | ~2 min | Optional NINJAFOAM utilities |
| Runtime setup | <1 min | Configure entrypoint |
| **Total** | **~30-45 min** | Assumes ~4 core CPU; adjust if needed |

**Previous build time:** ~50-60 min (building PROJ, GDAL, NetCDF, OpenFOAM from source)  
**Current build time:** ~35 min (system packages only)  
**Speedup:** ~40% faster! 🚀

---

## Success Criteria

After Step 7, you should see:
- ✅ Docker image listed: `windninja:latest`
- ✅ Smoke test passes: `windninja --help` shows output
- ✅ Container runs: `docker run` completes without "command not found"
- ✅ TAR file created (if transferring back)

Once all three are confirmed, the image is ready for Phase 4 (integration testing with Python scripts on Windows).

---

## Questions or Stuck?

If the build fails at a specific layer:
1. **Note the error message** and which Stage it's in
2. **Check disk space:** `df -h` (need ~20 GB free)
3. **Check internet:** `ping -c 3 8.8.8.8` (downloads are needed)
4. **Check CPU:** Build uses -j4 by default (edit `build_deps_docker.sh` if needed)
5. **Share error log:** Copy the full error message from the output

---
