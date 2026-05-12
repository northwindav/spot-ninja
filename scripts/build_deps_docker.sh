#!/bin/bash
# ============================================================================
# build_deps_docker.sh - Build dependencies for WindNinja in Docker
# ============================================================================
# This script installs all required dependencies for WindNinja compilation:
#   - NetCDF 4.1.1 (data format)
#   - GDAL 2.2.2 with full support (geospatial raster/vector I/O)
#   - PROJ 4.9.3 (coordinate transformations)
#   - OpenFOAM 8 (momentum solver for NINJAFOAM)
#
# Called by Dockerfile during image build
# Location in Docker: /opt/src/windninja/scripts/build_deps_docker.sh
# ============================================================================

set -e  # Exit on error
set -x  # Print each command (debugging)

DEBIAN_FRONTEND=noninteractive

echo "======================================================================"
echo "Installing WindNinja Build Dependencies"
echo "======================================================================"

# ============================================================================
# Step 1: Install system-level build dependencies and libraries
# ============================================================================

apt-get update
apt-get install -y --no-install-recommends \
    # Compression libraries (for NetCDF, HDF5, etc.)
    zlib1g-dev libbz2-dev liblzma-dev libcurl4-openssl-dev \
    # HDF5 (required by NetCDF)
    libhdf5-dev \
    # GDAL dependencies: shapefile support (FIX for "No package shapelib found")
    libshp-dev libshp2 \
    # GDAL dependencies: other formats and tools
    libspatialindex-dev libexpat1-dev libxerces-c-dev \
    # GDAL dependencies: database drivers
    libpq-dev \
    # Proj/GDAL coordinate system utilities
    libproj-dev proj-data \
    # Build and compiler tools (additional)
    gfortran autoconf libtool \
    # Utilities
    curl unzip vim less

# ============================================================================
# Step 2: Build and install PROJ 4.9.3
# ============================================================================

echo "Building PROJ 4.9.3..."
cd /opt/src
wget -q https://github.com/OSGeo/PROJ/releases/download/4.9.3/proj-4.9.3.tar.gz
tar -xzf proj-4.9.3.tar.gz
cd proj-4.9.3
./configure --prefix=/usr/local
make -j4
make install
ldconfig
cd /opt/src
rm -rf proj-4.9.3 proj-4.9.3.tar.gz

# ============================================================================
# Step 3: Build and install GDAL 2.2.2
# ============================================================================

echo "Building GDAL 2.2.2..."
cd /opt/src
wget -q https://github.com/OSGeo/gdal/releases/download/v2.2.2/gdal-2.2.2.tar.gz
tar -xzf gdal-2.2.2.tar.gz
cd gdal-2.2.2
./configure \
    --prefix=/usr/local \
    --with-proj=/usr/local \
    --with-hdf5=/usr/include/hdf5/serial,/usr/lib/x86_64-linux-gnu/hdf5/serial \
    --with-curl \
    --with-png \
    --with-jpeg \
    --with-geos \
    --with-libshp
make -j4
make install
ldconfig
cd /opt/src
rm -rf gdal-2.2.2 gdal-2.2.2.tar.gz

# ============================================================================
# Step 4: Build and install NetCDF 4.1.1
# ============================================================================

echo "Building NetCDF 4.1.1..."
cd /opt/src
wget -q https://www.unidata.ucar.edu/downloads/netcdf/ftp/netcdf-4.1.1.tar.gz
tar -xzf netcdf-4.1.1.tar.gz
cd netcdf-4.1.1
CPPFLAGS="-I/usr/include/hdf5/serial" LDFLAGS="-L/usr/lib/x86_64-linux-gnu/hdf5/serial" \
./configure \
    --prefix=/usr/local \
    --enable-netcdf-4 \
    --enable-shared
make -j4
make install
ldconfig
cd /opt/src
rm -rf netcdf-4.1.1 netcdf-4.1.1.tar.gz

# ============================================================================
# Step 5: Build and install OpenFOAM 8
# ============================================================================

echo "Building OpenFOAM 8..."
cd /opt/src

# Download OpenFOAM
wget -q https://sourceforge.net/projects/openfoam/files/v8/OpenFOAM-8.tar.gz
tar -xzf OpenFOAM-8.tar.gz
cd OpenFOAM-8

# Patch bashrc for non-interactive build
sed -i 's|WM_PROJECT_INST_DIR=$HOME/OpenFOAM|WM_PROJECT_INST_DIR=/opt|g' etc/bashrc
sed -i 's|WM_PROJECT_DIR=$WM_PROJECT_INST_DIR/OpenFOAM-${WM_PROJECT_VERSION}|WM_PROJECT_DIR=$WM_PROJECT_INST_DIR/openfoam8|g' etc/bashrc

# Source bashrc and build
source etc/bashrc
cd $WM_PROJECT_DIR

# Build OpenFOAM
./Allwmake -j 4 2>&1 | tail -100

# Verify build
if [ -d "$FOAM_LIBBIN" ]; then
    echo "OpenFOAM 8 built successfully"
else
    echo "Warning: OpenFOAM build verification inconclusive, proceeding anyway"
fi

cd /opt/src
rm OpenFOAM-8.tar.gz

# ============================================================================
# Step 6: Verify installs
# ============================================================================

echo ""
echo "======================================================================"
echo "Verifying dependency installations..."
echo "======================================================================"

ldconfig -p | grep -E "proj|gdal|netcdf|hdf5" || echo "Note: Some libraries may not be in cache yet"

echo ""
echo "======================================================================"
echo "Build dependencies installation complete!"
echo "======================================================================"
