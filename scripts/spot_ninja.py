"""
spot_ninja.py - Main orchestration script for Spot-Ninja (MVP)

Coordinates:
1. Input validation
2. DEM retrieval (CanElevation)
3. Weather data retrieval (MSC GeoMet)
4. Config generation
5. Docker container invocation
6. Output processing

Phase 4 implementation (placeholder)
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

from utils import setup_logging, load_config, get_data_paths, Config
from validators import validate_all
from dem_retriever import DEMRetriever
from weather_retriever import WeatherRetriever


def main():
    """Main entry point for Spot-Ninja."""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Spot-Ninja: WindNinja automation for Canadian forecasts",
        epilog="Example: python spot_ninja.py --lat 51 --lon -114 --config config/spot-ninja.yaml"
    )
    
    parser.add_argument("--lat", type=float, required=True, help="Center latitude")
    parser.add_argument("--lon", type=float, required=True, help="Center longitude")
    parser.add_argument("--config", type=Path, default=Path("config/spot-ninja.yaml"), 
                      help="Path to YAML config file")
    parser.add_argument("--env", type=Path, default=Path(".env"), 
                      help="Path to .env file")
    parser.add_argument("--data-dir", type=Path, default=Path("data"),
                      help="Base data directory")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                      default="INFO", help="Logging level")
    parser.add_argument("--skip-dem", action="store_true", help="Skip DEM download")
    parser.add_argument("--skip-weather", action="store_true", help="Skip weather download")
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = args.data_dir / "spot-ninja.log"
    logger = setup_logging(args.log_level, log_file)
    
    logger.info("=" * 60)
    logger.info("Spot-Ninja: WindNinja Automation Pipeline")
    logger.info("=" * 60)
    logger.info(f"Location: ({args.lat:.4f}, {args.lon:.4f})")
    logger.info(f"Config: {args.config}")
    
    # Load configuration
    try:
        config = Config(args.config, args.env)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Validate inputs
    logger.info("Validating inputs...")
    roi_km = config.roi_size()
    dem_config = config.dem_config()
    weather_config = config.weather_config()
    
    validation = validate_all(
        latitude=args.lat,
        longitude=args.lon,
        roi_km=roi_km,
        dem_collection=dem_config.get("collection", "hrdem-mosaic-1m"),
        model=weather_config.get("primary_model", "HRDPS"),
        resolution=weather_config.get("primary_resolution", "2.5km")
    )
    
    if not validation["valid"]:
        for error in validation["errors"]:
            logger.error(f"Validation error: {error}")
        return 1
    
    for warning in validation["warnings"]:
        logger.warning(warning)
    
    logger.info("✓ Inputs validated")
    
    # Get data paths
    data_paths = get_data_paths(args.data_dir)
    
    # Download DEM
    if not args.skip_dem:
        logger.info("Downloading DEM...")
        try:
            retriever = DEMRetriever(data_paths["dems"])
            dem_path = retriever.download_dem(
                args.lat, args.lon, roi_km,
                collection=dem_config.get("collection", "hrdem-mosaic-1m"),
                cascade=True
            )
            
            if dem_path and retriever.validate_dem(dem_path):
                logger.info(f"✓ DEM ready: {dem_path}")
            else:
                logger.error("DEM validation failed")
                return 1
        except Exception as e:
            logger.error(f"DEM retrieval failed: {e}")
            return 1
    else:
        logger.info("Skipping DEM download (--skip-dem)")
    
    # Download weather data
    if not args.skip_weather:
        logger.info("Downloading weather data...")
        try:
            retriever = WeatherRetriever(data_paths["weather"])
            forecast_path = retriever.download_forecast(
                model=weather_config.get("primary_model", "HRDPS"),
                resolution=weather_config.get("primary_resolution", "2.5km"),
                latitude=args.lat,
                longitude=args.lon
            )
            
            if forecast_path and retriever.validate_forecast(forecast_path):
                logger.info(f"✓ Weather data ready: {forecast_path}")
            else:
                logger.error("Forecast validation failed")
                return 1
        except Exception as e:
            logger.error(f"Weather retrieval failed: {e}")
            return 1
    else:
        logger.info("Skipping weather download (--skip-weather)")
    
    logger.info("=" * 60)
    logger.info("✓ Phase 3 (Data Retrieval) Complete")
    logger.info("Output files ready in: " + str(data_paths["output"]))
    logger.info("=" * 60)
    logger.info("\nNext steps (Phase 4):")
    logger.info("  1. Generate WindNinja config from template")
    logger.info("  2. Invoke Docker container")
    logger.info("  3. Process output (KMZ verification)")
    
    return 0


if __name__ == "__main__":
    exit(main())
