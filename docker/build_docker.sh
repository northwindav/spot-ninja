#!/bin/bash
# build_docker.sh - Build WindNinja Docker image for Spot-Ninja
# Usage: bash docker/build_docker.sh [--tag windninja:latest] [--no-cache]

set -e

# Parse arguments
TAG="windninja:latest"
BUILD_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            BUILD_ARGS="$BUILD_ARGS --no-cache"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Building WindNinja Docker image"
echo "=========================================="
echo "Tag:  $TAG"
echo "Args: $BUILD_ARGS"
echo ""

# Ensure we're in the project root
if [ ! -f "Dockerfile" ]; then
    if [ -f "docker/Dockerfile" ]; then
        cd docker
    else
        echo "ERROR: Dockerfile not found. Run from spot-ninja or docker directory."
        exit 1
    fi
fi

# Clone WindNinja if not already present
WINDNINJA_DIR="../windninja_source"
if [ ! -d "$WINDNINJA_DIR" ]; then
    echo "Cloning WindNinja source..."
    git clone https://github.com/firelab/windninja.git "$WINDNINJA_DIR"
else
    echo "Using existing WindNinja source at $WINDNINJA_DIR"
fi

# Build the image
echo ""
echo "Running: docker build -t $TAG $BUILD_ARGS -f Dockerfile .."
docker build -t $TAG $BUILD_ARGS -f Dockerfile "$WINDNINJA_DIR"

echo ""
echo "=========================================="
echo "Build complete!"
echo "Tag: $TAG"
echo ""
echo "Verify build:"
echo "  docker run --rm $TAG windninja --help"
echo ""
echo "Run with data:"
echo "  docker run -v \$(pwd)/data:/data $TAG windninja /data/config.sta"
echo "=========================================="
