# Ubuntu Docker Build Guide for Spot-Ninja

**Status:** Building WindNinja Docker image locally on Ubuntu machine (due to GitHub Actions failure with missing `shapelib`)

## Phase: Build Environment Setup & Docker Compilation

---

## Prerequisites Check

Before starting, verify you have:
- [ ] Ubuntu machine with internet access
- [ ] `sudo` access (required for Docker installation)
- [ ] ~20 GB free disk space (for build artifacts + Docker image)
- [ ] ~45-60 minutes for full build

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

The Dockerfile has 4 stages:

| Stage | Purpose | Duration |
|-------|---------|----------|
| 1: System Deps | Install build tools + call `build_deps_docker.sh` | ~15 min |
| 2: WindNinja Compile | CMake + make WindNinja binary | ~20 min |
| 3: OpenFOAM Setup | Copy NINJAFOAM libraries into OpenFOAM | ~5 min |
| 4: Runtime Setup | Configure entrypoint + environment | <1 min |

**Key fix in this build:** `build_deps_docker.sh` now includes `libshp-dev` (shapefile library), which was causing the GitHub Actions failure.

---

## Step 5: Build the Docker Image

```bash
# Navigate to the spot-ninja repo (if not already there)
cd ~/path/to/spot-ninja

# Build the image (this will take 30-50 minutes)
sudo docker build -t windninja:latest -f docker/Dockerfile .

# Monitor progress in real-time (watch the output)
# You'll see:
#   Step 1/4 : FROM ubuntu:20.04
#   Step 2/4 : RUN dpkg-reconfigure... (installing apt packages)
#   Step 3/4 : RUN mkdir -p /opt/src... (building PROJ, GDAL, NetCDF, OpenFOAM)
#   Step 4/4 : RUN mkdir -p /data... (setting up runtime)
```

**If build fails:**
- Check the error message for the exact line
- Note the error and we'll debug it
- You can re-run the build (Docker caches layers, so it's faster on retry)

**Expected output when complete:**
```
Successfully built abc123def456
Successfully tagged windninja:latest
```

---

## Step 6: Verify the Image

```bash
# List Docker images
sudo docker images | grep windninja
# Should show: windninja    latest    abc123def456    5 minutes ago    ~3-4 GB

# Test the image (smoke test)
sudo docker run --rm windninja:latest windninja --help
# Should output WindNinja help text
```

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
| `permission denied` | User not in docker group | Run Step 2 or use `sudo docker` |
| `build_deps_docker.sh: not found` | Script path issue | Verify script is at `docker/build_deps_docker.sh` |
| `Err:X ... No package shaeplib found` | **This was the GitHub Actions error** | Fixed in build_deps_docker.sh; re-run build |
| `make: g++: command not found` | build-essential not installed | build_deps_docker.sh handles this; re-run build |
| `out of disk space` | Build artifacts too large | Free up space, retry |
| OpenFOAM build fails | Compiler flags or dependencies | Continue anyway (non-critical for MVP) |

---

## Next Steps After Successful Build

1. **Test on Ubuntu:** Verify `docker run` works with sample data
2. **Transfer TAR file:** If needed for Windows, transfer `windninja-image.tar.gz`
3. **On Windows (Phase 4):** Load image and integrate with Python scripts
4. **Integration test:** Run `scripts/spot_ninja.py` with real locations

---

## Reference: Dockerfile Build Stages Explained

### Stage 1: System Dependencies (from Dockerfile)
```dockerfile
RUN apt-get install -y ... \
    && bash /opt/src/windninja/scripts/build_deps_docker.sh
```
**What it does:** 
- Installs cmake, git, build-essential, Boost, Python
- Calls our `build_deps_docker.sh` which builds PROJ, GDAL, NetCDF, OpenFOAM

### Stage 2: WindNinja Compilation
```dockerfile
RUN mkdir -p /opt/src/windninja/build && \
    cd /opt/src/windninja/build && \
    cmake [flags] && make -j12 && make install
```
**What it does:**
- Creates build directory
- Runs CMake with flags: NINJAFOAM=ON, NINJA_GUI=OFF, BUILD_FETCH_DEM=ON, etc.
- Compiles WindNinja binary (~20 minutes)
- Installs to `/usr/local/bin/windninja`

### Stage 3: OpenFOAM Setup
```dockerfile
RUN source /opt/openfoam8/etc/bashrc && \
    cp -r windninja FOAM apps && \
    wmake libso
```
**What it does:**
- Copies NINJAFOAM utilities into OpenFOAM directory
- Compiles NINJAFOAM momentum solver extensions

### Stage 4: Runtime Setup
```dockerfile
WORKDIR /data
ENTRYPOINT ["windninja"]
```
**What it does:**
- Sets working directory to `/data` (volume mount point)
- Default command is `windninja --help` if no args provided

---

## Build Time Estimate

| Stage | Duration | Notes |
|-------|----------|-------|
| apt-get install | ~2 min | Base packages |
| PROJ 4.9.3 | ~3 min | Coordinate system library |
| GDAL 2.2.2 | ~5 min | Geospatial I/O (shapefile fix here) |
| NetCDF 4.1.1 | ~3 min | Data format library |
| OpenFOAM 8 | ~15 min | Momentum solver (heaviest) |
| WindNinja compile | ~20 min | Main application |
| OpenFOAM setup + cleanup | ~5 min | Library copying |
| **Total** | **~50 min** | Assumes 4-core CPU; adjust -j12 if needed |

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
