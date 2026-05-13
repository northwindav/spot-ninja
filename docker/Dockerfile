# Spot-Ninja WindNinja Dockerfile
# Based on: https://github.com/firelab/windninja/blob/master/Dockerfile
# Customized for Canadian DEM/weather data with host-orchestrated workflow
#
# Build: docker build -t windninja:latest .
# Run:   docker run -v $(pwd)/data:/data windninja:latest windninja /data/config.sta
#
# Copyright (c) Kyle Shannon (WindNinja)
# Modified for Spot-Ninja project

# ============================================================================
# BUILD CONFIGURATION FOR SPOT-NINJA MVP
# ============================================================================
# CMake Flags Selected:
#   NINJAFOAM=ON                  - Momentum solver (required)
#   NINJA_GUI=OFF                 - CLI only (faster build, no Qt dependency)
#   BUILD_FETCH_DEM=ON            - DEM download capability
#   BUILD_SLOPE_ASPECT_GRID=ON    - Terrain analysis
#   BUILD_FLOW_SEPARATION_GRID=ON - Wind flow modeling
#   SUPRESS_WARNINGS=ON           - Clean build output
#
# Data Exchange:
#   /data volume mount (host <-> container)
#   Input:  DEMs, weather files in /data/dems, /data/weather
#   Output: KMZ results in /data/output
# ============================================================================

FROM ubuntu:24.04

USER root
SHELL [ "/usr/bin/bash", "-c" ]

# Non-interactive build
ENV DEBIAN_FRONTEND=noninteractive
ENV WM_PROJECT_INST_DIR=/opt
ENV WINDNINJA_DATA=/opt/src/windninja/data
ENV WINDNINJA_WORKDIR=/data

# ============================================================================
# STAGE 1: System Dependencies
# ============================================================================

WORKDIR /opt/src

# Install base build tools (needed for git clone)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget gnupg2 cmake git apt-transport-https ca-certificates \
    software-properties-common sudo build-essential \
    pkg-config g++ bash curl \
    libboost-program-options-dev \
    libboost-date-time-dev \
    libboost-test-dev \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Clone WindNinja v3.12.2 from official repository (latest stable - fixed Qt optional requirement)
RUN git clone --branch 3.12.2 https://github.com/firelab/windninja.git /opt/src/windninja

# Install all remaining build dependencies (inline from build_deps_docker.sh)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gfortran autoconf libtool \
    libhdf5-dev \
    libnetcdf-dev \
    libgdal-dev \
    libproj-dev proj-data \
    libgeos-dev libgeos++-dev \
    libshp-dev \
    libpq-dev \
    libexpat1-dev libxerces-c-dev libspatialindex-dev \
    openfoam && \
    rm -rf /var/lib/apt/lists/*

# ============================================================================
# STAGE 2: WindNinja Compilation
# ============================================================================

RUN mkdir -p /opt/src/windninja/build && \
    cd /opt/src/windninja/build && \
    # CMake configuration with Spot-Ninja flags
    cmake \
    -D SUPRESS_WARNINGS=ON \
    -D NINJAFOAM=ON \
    -D BUILD_FETCH_DEM=ON \
    -D BUILD_SLOPE_ASPECT_GRID=ON \
    -D BUILD_FLOW_SEPARATION_GRID=ON \
    -D NINJA_GUI=OFF \
    .. && \
    # Parallel build (adjust -j12 based on host CPU cores)
    make -j12 && \
    make install && \
    ldconfig && \
    cd /opt/src/windninja

# ============================================================================
# STAGE 3: OpenFOAM NinjaFOAM Setup (optional, for momentum solver)
# ============================================================================

# Try to source system OpenFOAM environment if available
# The NinjaFOAM custom libraries may or may not compile with system package
# This stage is optional; WindNinja will still work without it
RUN bash -c 'if [ -f /usr/lib/openfoam/bashrc ]; then \
    source /usr/lib/openfoam/bashrc && \
    mkdir -p /opt/windninja_foam && \
    cp -r /opt/src/windninja/src/ninjafoam /opt/windninja_foam/ 2>/dev/null || true; \
fi' || echo "OpenFOAM NinjaFOAM setup skipped (system package may not have dev files)"

# ============================================================================
# STAGE 4: Runtime Setup
# ============================================================================

# Set working directory to data volume mount point
WORKDIR /data

# Ensure /data directory exists
RUN mkdir -p /data

# Expose environment variables for runtime configuration
ENV CPL_DEBUG=""
ENV WINDNINJA_CLI_SRTM_API_KEY=""
ENV CUSTOM_SRTM_API_KEY=""
ENV NINJA_FILL_DEM_NO_DATA=OFF

# Default entrypoint: windninja binary
# Usage: docker run windninja:latest windninja [options] <config_file>
ENTRYPOINT ["windninja"]
CMD ["--help"]

# ============================================================================
# NOTES
# ============================================================================
#
# Environment Variables (set at runtime with -e flag):
#   CPL_DEBUG=NINJAFOAM      - Enable OpenFOAM debug output
#   CPL_DEBUG=STABILITY      - Enable stability model debugging
#   CPL_DEBUG=GTIFF          - Enable GeoTIFF output debugging
#   CUSTOM_SRTM_API_KEY      - For DEM auto-download (if needed)
#
# Volume Mounts:
#   -v ./data:/data          - Data exchange directory
#
# Examples:
#   # Basic run with input files in /data
#   docker run -v $(pwd)/data:/data windninja:latest windninja /data/config.sta
#
#   # Run with stability debugging
#   docker run -e CPL_DEBUG=STABILITY -v $(pwd)/data:/data windninja:latest windninja /data/config.sta
#
#   # OpenFOAM debugging
#   docker run -e CPL_DEBUG=NINJAFOAM -v $(pwd)/data:/data windninja:latest windninja /data/config.sta
#
# Singularity Conversion (Phase 2 future):
#   docker build -t windninja:latest .
#   singularity build windninja_latest.sif docker-daemon://windninja:latest
