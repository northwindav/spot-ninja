"""
dem_retriever.py - Download Digital Elevation Models from CanElevation AWS S3

Source: CanElevation - Canada Digital Elevation Models
Registry: https://registry.opendata.aws/canelevation-dem/
License: Open Government License (Canada)

Supports:
- HRDEM Mosaic 1m (highest resolution)
- HRDEM Mosaic 2m
- MRDEM 30m (fallback, nationwide complete coverage)
- HRDEM LiDAR (project-based)
- HRDEM ArcticDEM (Northern Canada)

Access: AWS S3 buckets (no authentication required)
STAC Catalog: https://datacube.services.geo.ca/stac/api/
"""

import logging
import os
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    raise ImportError("boto3 required. Install: pip install boto3")

try:
    import rasterio
    from rasterio.io import MemoryFile
except ImportError:
    raise ImportError("rasterio required. Install: pip install rasterio")

logger = logging.getLogger(__name__)

# AWS S3 configuration
AWS_REGION = "ca-central-1"
CANELEVATION_BUCKET = "canelevation-dem"

# Collection configurations
COLLECTIONS = {
    "hrdem-mosaic-1m": {
        "prefix": "hrdem-mosaic-1m/",
        "resolution": 1,
        "description": "1m resolution mosaic (LiDAR + optical stereo)",
    },
    "hrdem-mosaic-2m": {
        "prefix": "hrdem-mosaic-2m/",
        "resolution": 2,
        "description": "2m resolution mosaic (LiDAR + optical stereo)",
    },
    "mrdem-30": {
        "prefix": "mrdem-30/",
        "resolution": 30,
        "description": "30m medium resolution (Copernicus + LiDAR)",
    },
    "hrdem-lidar": {
        "prefix": "hrdem-lidar/",
        "resolution": "variable",
        "description": "LiDAR acquisition project-based HR DEM",
    },
    "hrdem-arcticdem": {
        "prefix": "hrdem-arcticdem/",
        "resolution": 2,
        "description": "2m Arctic DEM (optical stereo, Northern Canada)",
    },
}

# Cascade order (primary -> fallback)
COLLECTION_CASCADE = ["hrdem-mosaic-1m", "hrdem-mosaic-2m", "mrdem-30"]


class DEMRetriever:
    """Download and manage Digital Elevation Models from CanElevation."""

    def __init__(self, output_dir: Path, region: str = AWS_REGION):
        """
        Initialize DEM retriever.

        Args:
            output_dir (Path): Directory to save downloaded DEMs
            region (str): AWS region
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.region = region
        
        # Initialize S3 client (no credentials required for public buckets)
        self.s3_client = boto3.client("s3", region_name=region)
        logger.info(f"Initialized DEM retriever (output: {self.output_dir})")

    def get_available_collections(self) -> Dict[str, dict]:
        """
        Get list of available collections.

        Returns:
            Dict[str, dict]: Collection metadata
        """
        return COLLECTIONS.copy()

    def bbox_from_latlon(self, latitude: float, longitude: float, 
                        roi_km: float) -> Tuple[float, float, float, float]:
        """
        Convert lat/lon + ROI size to bounding box.

        Accounts for varying degree sizes in Canada (latitude != km).

        Args:
            latitude (float): Center latitude
            longitude (float): Center longitude
            roi_km (float): ROI radius in km

        Returns:
            Tuple[float, float, float, float]: (min_lon, min_lat, max_lon, max_lat)
        """
        # Approximate: 1 degree latitude ≈ 111 km; 1 degree longitude varies by latitude
        lat_delta = roi_km / 111.0
        lon_delta = roi_km / (111.0 * abs(__import__("math").cos(__import__("math").radians(latitude))))

        min_lon = longitude - lon_delta
        max_lon = longitude + lon_delta
        min_lat = latitude - lat_delta
        max_lat = latitude + lat_delta

        logger.debug(f"BBox: lat [{min_lat:.4f}, {max_lat:.4f}], lon [{min_lon:.4f}, {max_lon:.4f}]")
        return min_lon, min_lat, max_lon, max_lat

    def list_tiles_in_bbox(self, collection: str, bbox: Tuple[float, float, float, float]) -> List[str]:
        """
        List DEM tiles within a bounding box.

        Note: This is a mock implementation. Real implementation would query STAC catalog
        or list S3 objects matching the bbox region.

        Args:
            collection (str): Collection name
            bbox (Tuple[float, float, float, float]): (min_lon, min_lat, max_lon, max_lat)

        Returns:
            List[str]: List of tile file paths in S3
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        if collection not in COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection}")

        prefix = COLLECTIONS[collection]["prefix"]
        logger.info(f"Listing tiles in {collection} for bbox: lat [{min_lat:.2f}, {max_lat:.2f}], lon [{min_lon:.2f}, {max_lon:.2f}]")

        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=CANELEVATION_BUCKET, Prefix=prefix)

            tiles = []
            for page in pages:
                if "Contents" not in page:
                    continue
                for obj in page["Contents"]:
                    key = obj["Key"]
                    # Filter by filename pattern (GeoTIFF files)
                    if key.endswith(".tif") or key.endswith(".tiff"):
                        tiles.append(key)

            logger.info(f"Found {len(tiles)} tiles in {collection}")
            return tiles
        except ClientError as e:
            logger.error(f"S3 error listing tiles: {e}")
            raise

    def download_tile(self, s3_key: str, local_path: Path) -> bool:
        """
        Download a single DEM tile from S3.

        Args:
            s3_key (str): S3 object key
            local_path (Path): Local file path to save

        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Downloading: {s3_key}")
            self.s3_client.download_file(
                Bucket=CANELEVATION_BUCKET,
                Key=s3_key,
                Filename=str(local_path)
            )
            logger.info(f"Saved: {local_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download {s3_key}: {e}")
            return False

    def download_dem(self, latitude: float, longitude: float, roi_km: float,
                    collection: str = "hrdem-mosaic-1m", cascade: bool = True) -> Optional[Path]:
        """
        Download DEM for location and ROI.

        Args:
            latitude (float): Center latitude
            longitude (float): Center longitude
            roi_km (float): ROI radius in km
            collection (str): Preferred collection ("hrdem-mosaic-1m", etc.)
            cascade (bool): If True, fallback to lower-res collections if needed

        Returns:
            Optional[Path]: Path to downloaded DEM file, or None if failed
        """
        # Calculate bounding box
        bbox = self.bbox_from_latlon(latitude, longitude, roi_km)
        min_lon, min_lat, max_lon, max_lat = bbox

        # Determine collections to try
        collections_to_try = [collection]
        if cascade:
            # Add fallback collections
            for col in COLLECTION_CASCADE:
                if col != collection and col not in collections_to_try:
                    collections_to_try.append(col)

        # Try each collection
        for col in collections_to_try:
            logger.info(f"Trying collection: {col}")

            try:
                tiles = self.list_tiles_in_bbox(col, bbox)
                if not tiles:
                    logger.warning(f"No tiles found in {col}; trying fallback")
                    continue

                # Download first tile (MVP: single tile per query)
                # In production, mosaic multiple tiles
                output_path = self.output_dir / f"dem_{col}_{latitude:.2f}_{longitude:.2f}.tif"
                
                if self.download_tile(tiles[0], output_path):
                    logger.info(f"Successfully downloaded DEM from {col}")
                    return output_path

            except Exception as e:
                logger.warning(f"Failed with {col}: {e}")
                continue

        logger.error(f"Failed to download DEM after trying {collections_to_try}")
        return None

    def validate_dem(self, dem_path: Path) -> bool:
        """
        Validate downloaded DEM file.

        Args:
            dem_path (Path): Path to DEM file

        Returns:
            bool: True if valid
        """
        try:
            with rasterio.open(dem_path) as src:
                # Check dimensions
                if src.width < 2 or src.height < 2:
                    logger.error(f"DEM too small: {src.width}x{src.height}")
                    return False

                # Check CRS (should be geographic or UTM)
                if src.crs is None:
                    logger.warning(f"DEM has no CRS defined")

                # Check for data
                data = src.read(1)
                if data.size == 0:
                    logger.error("DEM has no data")
                    return False

                logger.info(f"DEM valid: {src.width}x{src.height}, CRS={src.crs}, bounds={src.bounds}")
                return True
        except Exception as e:
            logger.error(f"DEM validation failed: {e}")
            return False


def demo():
    """Demonstration of DEM retriever usage."""
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    # Test location: Alberta Foothills
    latitude, longitude, roi_km = 51.0, -114.0, 10.0
    
    with tempfile.TemporaryDirectory() as tmpdir:
        retriever = DEMRetriever(Path(tmpdir))
        
        print(f"\n=== Downloading DEM for ({latitude}, {longitude}) ===")
        dem_path = retriever.download_dem(latitude, longitude, roi_km)
        
        if dem_path and dem_path.exists():
            print(f"✓ DEM downloaded: {dem_path}")
            if retriever.validate_dem(dem_path):
                print(f"✓ DEM validated")
            else:
                print(f"✗ DEM validation failed")
        else:
            print(f"✗ DEM download failed")


if __name__ == "__main__":
    demo()
