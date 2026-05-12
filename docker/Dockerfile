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

FROM ubuntu:20.04

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

# Copy WindNinja source
ADD . /opt/src/windninja/

# Install base build tools and libraries
RUN dpkg-reconfigure debconf --frontend=noninteractive && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    wget gnupg2 cmake git apt-transport-https ca-certificates \
    software-properties-common sudo build-essential \
    pkg-config g++ \
    libboost-program-options-dev \
    libboost-date-time-dev \
    libboost-test-dev \
    python3-pip && \
    cd /opt/src && \
    # Build all dependencies (NetCDF, GDAL, OpenFOAM, etc.)
    DEBIAN_FRONTEND=noninteractive /opt/src/windninja/scripts/build_deps_docker.sh && \
    # Clean package manager cache to reduce image size
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
# STAGE 3: OpenFOAM Compilation & Setup
# ============================================================================

RUN source /opt/openfoam8/etc/bashrc && \
    mkdir -p $FOAM_RUN/../applications && \
    cp -r /opt/src/windninja/src/ninjafoam/8/* $FOAM_RUN/../applications && \
    cd $FOAM_RUN/../applications/ && \
    sed -i "s|export WM_PROJECT_INST_DIR=|export WM_PROJECT_INST_DIR=/opt|g" \
    /opt/openfoam8/etc/bashrc && \
    sed -i "s|export WM_PROJECT_DIR=\$WM_PROJECT_INST_DIR/openfoam8|export WM_PROJECT_DIR=/opt/openfoam8|g" \
    /opt/openfoam8/etc/bashrc && \
    . /opt/openfoam8/etc/bashrc && \
    wmake libso && \
    cd utility/applyInit && \
    wmake && \
    # Copy custom WindNinja OpenFOAM libraries (Singularity compatibility)
    cp $FOAM_RUN/../platforms/linux64GccDPInt32Opt/lib/libWindNinja.so \
    /opt/openfoam8/platforms/linux64GccDPInt32Opt/lib/ && \
    cp $FOAM_RUN/../platforms/linux64GccDPInt32Opt/bin/applyInit \
    /opt/openfoam8/platforms/linux64GccDPInt32Opt/bin/ && \
    chmod 644 /opt/openfoam8/platforms/linux64GccDPInt32Opt/lib/libWindNinja.so && \
    chmod 755 /opt/openfoam8/platforms/linux64GccDPInt32Opt/bin/applyInit

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
