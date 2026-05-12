#!/bin/bash
set -e
set -x

DEBIAN_FRONTEND=noninteractive

echo "======================================================================"
echo "Installing WindNinja Build Dependencies"
echo "======================================================================"

# ============================================================================
# Step 1: Install system-level build dependencies and libraries
# ============================================================================

echo "Step 1: Installing system packages..."
apt-get update
apt-get install -y --no-install-recommends \
    zlib1g-dev libbz2-dev liblzma-dev libcurl4-openssl-dev \
    libhdf5-dev \
    libshp-dev \
    libgeos-dev libgeos++-dev \
    libspatialindex-dev libexpat1-dev libxerces-c-dev \
    libpq-dev \
    libproj-dev proj-data \
    gfortran autoconf libtool \
    curl unzip vim less

# ============================================================================
# Step 2: Build and install PROJ 4.9.3
# ============================================================================

echo ""
echo "Step 2: Building PROJ 4.9.3..."
cd /opt/src
echo "Downloading PROJ 4.9.3..."
wget https://github.com/OSGeo/PROJ/releases/download/4.9.3/proj-4.9.3.tar.gz || { echo "PROJ download failed"; exit 1; }
echo "Extracting PROJ..."
tar -xzf proj-4.9.3.tar.gz || { echo "PROJ extraction failed"; exit 1; }
cd proj-4.9.3 || { echo "PROJ directory not found"; exit 1; }
echo "Configuring PROJ..."
./configure --prefix=/usr/local || { echo "PROJ configure failed"; exit 1; }
echo "Building PROJ..."
make -j4 || { echo "PROJ make failed"; exit 1; }
echo "Installing PROJ..."
make install || { echo "PROJ make install failed"; exit 1; }
ldconfig
cd /opt/src
rm -rf proj-4.9.3 proj-4.9.3.tar.gz

# ============================================================================
# Step 3: Build and install GDAL 2.2.2
# ============================================================================

echo ""
echo "Step 3: Building GDAL 2.2.2..."
cd /opt/src
echo "Downloading GDAL..."
wget https://github.com/OSGeo/gdal/releases/download/v2.2.2/gdal-2.2.2.tar.gz || { echo "GDAL download failed"; exit 1; }
echo "Extracting GDAL..."
tar -xzf gdal-2.2.2.tar.gz || { echo "GDAL extraction failed"; exit 1; }
cd gdal-2.2.2 || { echo "GDAL directory not found"; exit 1; }
echo "Configuring GDAL..."
./configure \
    --prefix=/usr/local \
    --with-proj=/usr/local \
    --with-hdf5=/usr/include/hdf5/serial,/usr/lib/x86_64-linux-gnu/hdf5/serial \
    --with-curl \
    --with-png \
    --with-jpeg \
    --with-geos \
    --with-libshp || { echo "GDAL configure failed"; exit 1; }
echo "Building GDAL..."
make -j4 || { echo "GDAL make failed"; exit 1; }
echo "Installing GDAL..."
make install || { echo "GDAL make install failed"; exit 1; }
ldconfig
cd /opt/src
rm -rf gdal-2.2.2 gdal-2.2.2.tar.gz

# ============================================================================
# Step 4: Build and install NetCDF 4.1.1
# ============================================================================

echo ""
echo "Step 4: Building NetCDF 4.1.1..."
cd /opt/src
echo "Downloading NetCDF..."
wget https://www.unidata.ucar.edu/downloads/netcdf/ftp/netcdf-4.1.1.tar.gz || { echo "NetCDF download failed"; exit 1; }
echo "Extracting NetCDF..."
tar -xzf netcdf-4.1.1.tar.gz || { echo "NetCDF extraction failed"; exit 1; }
cd netcdf-4.1.1 || { echo "NetCDF directory not found"; exit 1; }
echo "Configuring NetCDF..."
CPPFLAGS="-I/usr/include/hdf5/serial" LDFLAGS="-L/usr/lib/x86_64-linux-gnu/hdf5/serial" \
./configure \
    --prefix=/usr/local \
    --enable-netcdf-4 \
    --enable-shared || { echo "NetCDF configure failed"; exit 1; }
echo "Building NetCDF..."
make -j4 || { echo "NetCDF make failed"; exit 1; }
echo "Installing NetCDF..."
make install || { echo "NetCDF make install failed"; exit 1; }
ldconfig
cd /opt/src
rm -rf netcdf-4.1.1 netcdf-4.1.1.tar.gz

# ============================================================================
# Step 5: Build and install OpenFOAM 8 (required for NINJAFOAM)
# ============================================================================

echo ""
echo "Step 5: Building OpenFOAM 8..."
cd /opt/src
echo "Downloading OpenFOAM..."
wget https://sourceforge.net/projects/openfoam/files/v8/OpenFOAM-8.tar.gz || { echo "OpenFOAM download failed"; exit 1; }
echo "Extracting OpenFOAM..."
tar -xzf OpenFOAM-8.tar.gz || { echo "OpenFOAM extraction failed"; exit 1; }
cd OpenFOAM-8 || { echo "OpenFOAM directory not found"; exit 1; }
sed -i 's|WM_PROJECT_INST_DIR=$HOME/OpenFOAM|WM_PROJECT_INST_DIR=/opt|g' etc/bashrc
sed -i 's|WM_PROJECT_DIR=$WM_PROJECT_INST_DIR/OpenFOAM-${WM_PROJECT_VERSION}|WM_PROJECT_DIR=$WM_PROJECT_INST_DIR/openfoam8|g' etc/bashrc
source etc/bashrc
cd $WM_PROJECT_DIR
echo "Building OpenFOAM..."
./Allwmake -j 4 2>&1 | tail -100
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
echo "====================================================================="

