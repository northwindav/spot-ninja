"""
weather_retriever.py - Download weather forecast data from MSC GeoMet API

Source: Meteorological Service of Canada (MSC) GeoMet
API: https://api.weather.gc.ca/
Documentation: https://eccc-msc.github.io/open-data/msc-geomet/readme_en/
License: Open Government License (Canada)

Supports:
- HRDPS (High Resolution Deterministic Prediction System)
  - 1.0 km resolution (limited areas)
  - 2.5 km resolution (continental domain)
- GDPS (Global Deterministic Prediction System)
  - 10 km resolution (worldwide)

No authentication required for basic access.
"""

import logging
import os
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from datetime import datetime, timedelta
import re

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    raise ImportError("requests required. Install: pip install requests")

try:
    import xarray as xr
    import netCDF4
except ImportError:
    raise ImportError("xarray and netCDF4 required. Install: pip install xarray netCDF4")

logger = logging.getLogger(__name__)

# MSC GeoMet API configuration
GEOMET_API_BASE = "https://api.weather.gc.ca"
GEOMET_COVERAGE_BASE = "https://api.weather.gc.ca/coverages"

# Available models and their collections
MODELS = {
    "HRDPS": {
        "1.0km": {
            "collection": "hrdps-continental-1km",
            "resolution": 1.0,
            "domain": "continental_1km",
            "description": "1km high-resolution (limited regional areas)",
        },
        "2.5km": {
            "collection": "hrdps-continental",
            "resolution": 2.5,
            "domain": "continental",
            "description": "2.5km continental domain (most of Canada)",
        },
    },
    "GDPS": {
        "10km": {
            "collection": "gdps",
            "resolution": 10.0,
            "domain": "global",
            "description": "10km global domain",
        },
    },
}

# Required meteorological variables for WindNinja
REQUIRED_VARIABLES = ["u", "v", "t"]  # u-wind, v-wind, temperature
OPTIONAL_VARIABLES = ["rh", "precip"]  # relative humidity, precipitation


class WeatherRetriever:
    """Download and manage weather forecast data from MSC GeoMet."""

    def __init__(self, output_dir: Path, api_base: str = GEOMET_API_BASE):
        """
        Initialize weather retriever.

        Args:
            output_dir (Path): Directory to save downloaded data
            api_base (str): GeoMet API base URL
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_base = api_base

        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info(f"Initialized weather retriever (output: {self.output_dir})")

    def get_available_models(self) -> Dict[str, dict]:
        """Get list of available models and resolutions."""
        return MODELS.copy()

    def get_latest_forecast_time(self, model: str) -> Optional[str]:
        """
        Get the latest available forecast issue time.

        For HRDPS: typically 4 times per day (00, 06, 12, 18 UTC)
        For GDPS: typically 2 times per day (00, 12 UTC)

        Args:
            model (str): Model name ("HRDPS" or "GDPS")

        Returns:
            Optional[str]: ISO timestamp of latest forecast (e.g., "2024-05-11T12:00:00Z"), or None if failed
        """
        try:
            url = f"{self.api_base}/collections/{MODELS[model]['2.5km']['collection']}/items"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            if "features" in data and len(data["features"]) > 0:
                # Features are typically sorted newest first
                latest = data["features"][0]
                issue_time = latest.get("properties", {}).get("datetime")
                logger.info(f"Latest {model} forecast: {issue_time}")
                return issue_time

            logger.warning(f"No forecast data found for {model}")
            return None

        except Exception as e:
            logger.error(f"Failed to get latest forecast time for {model}: {e}")
            return None

    def query_coverage(self, model: str, resolution: str, 
                      latitude: float, longitude: float,
                      forecast_hours: Tuple[int, int] = (12, 36),
                      variables: List[str] = None) -> Optional[Dict]:
        """
        Query GeoMet API for weather data.

        Args:
            model (str): Model name ("HRDPS" or "GDPS")
            resolution (str): Resolution ("1.0km", "2.5km", "10km")
            latitude (float): Center latitude
            longitude (float): Center longitude
            forecast_hours (Tuple[int, int]): (start_hour, end_hour) forecast range
            variables (List[str]): Variables to request (default: REQUIRED_VARIABLES)

        Returns:
            Optional[Dict]: Coverage data with variable URLs, or None if failed
        """
        if variables is None:
            variables = REQUIRED_VARIABLES

        if model not in MODELS or resolution not in MODELS[model]:
            logger.error(f"Invalid model/resolution: {model}/{resolution}")
            return None

        model_config = MODELS[model][resolution]
        collection = model_config["collection"]

        # Get latest forecast time
        forecast_time = self.get_latest_forecast_time(model)
        if not forecast_time:
            logger.error(f"Could not determine forecast time for {model}")
            return None

        # Query each variable
        coverage_data = {
            "model": model,
            "resolution": resolution,
            "forecast_time": forecast_time,
            "location": {"lat": latitude, "lon": longitude},
            "variables": {}
        }

        for var in variables:
            try:
                # Construct coverage query
                # Example: https://api.weather.gc.ca/coverages/hrdps-continental/query?...
                params = {
                    "skipGeometry": "true",
                    "coords": f"POINT({longitude} {latitude})",
                    "f": "json",
                    "datetime": forecast_time,
                }

                url = f"{self.api_base}/coverages/{collection}/{var}"
                logger.debug(f"Querying: {url}")
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()

                data = response.json()
                if "value" in data:
                    coverage_data["variables"][var] = {
                        "value": data["value"],
                        "url": response.url,
                    }
                    logger.info(f"Retrieved {var} from {model}/{resolution}")
                else:
                    logger.warning(f"No data for variable {var}")

            except Exception as e:
                logger.warning(f"Failed to get {var} from {model}: {e}")
                continue

        if not coverage_data["variables"]:
            logger.error(f"No variables retrieved for {model}/{resolution}")
            return None

        return coverage_data

    def download_forecast(self, model: str, resolution: str,
                         latitude: float, longitude: float,
                         forecast_hours: Tuple[int, int] = (12, 36)) -> Optional[Path]:
        """
        Download weather forecast data.

        Args:
            model (str): Model name
            resolution (str): Resolution
            latitude (float): Latitude
            longitude (float): Longitude
            forecast_hours (Tuple[int, int]): Forecast range

        Returns:
            Optional[Path]: Path to saved forecast file, or None if failed
        """
        try:
            logger.info(f"Downloading {model} {resolution} forecast for ({latitude}, {longitude})")

            # Query coverage
            coverage = self.query_coverage(model, resolution, latitude, longitude, forecast_hours)
            if not coverage:
                return None

            # Save as JSON metadata file
            output_path = self.output_dir / f"forecast_{model}_{resolution}_{latitude:.2f}_{longitude:.2f}.json"
            with open(output_path, "w") as f:
                json.dump(coverage, f, indent=2)

            logger.info(f"Saved forecast metadata: {output_path}")

            # In production, would also download NetCDF/GeoTIFF files
            # For now, return metadata file path
            return output_path

        except Exception as e:
            logger.error(f"Failed to download forecast: {e}")
            return None

    def validate_forecast(self, forecast_path: Path) -> bool:
        """
        Validate downloaded forecast file.

        Args:
            forecast_path (Path): Path to forecast file

        Returns:
            bool: True if valid
        """
        try:
            if forecast_path.suffix == ".json":
                # Validate JSON metadata
                with open(forecast_path) as f:
                    data = json.load(f)

                required_keys = ["model", "resolution", "variables", "forecast_time"]
                if not all(k in data for k in required_keys):
                    logger.error(f"Forecast missing required keys")
                    return False

                if not data["variables"]:
                    logger.error(f"Forecast has no variables")
                    return False

                logger.info(f"Forecast metadata valid: {data['model']}/{data['resolution']}, vars={list(data['variables'].keys())}")
                return True

            else:
                # For NetCDF/GeoTIFF files (future)
                logger.warning("Only JSON validation implemented")
                return True

        except Exception as e:
            logger.error(f"Forecast validation failed: {e}")
            return False


def demo():
    """Demonstration of weather retriever usage."""
    import tempfile

    logging.basicConfig(level=logging.INFO)

    # Test location: Alberta Foothills
    latitude, longitude = 51.0, -114.0

    with tempfile.TemporaryDirectory() as tmpdir:
        retriever = WeatherRetriever(Path(tmpdir))

        print(f"\n=== Downloading HRDPS forecast for ({latitude}, {longitude}) ===")
        forecast_path = retriever.download_forecast("HRDPS", "2.5km", latitude, longitude)

        if forecast_path and forecast_path.exists():
            print(f"✓ Forecast downloaded: {forecast_path}")
            if retriever.validate_forecast(forecast_path):
                print(f"✓ Forecast validated")
            else:
                print(f"✗ Forecast validation failed")
        else:
            print(f"✗ Forecast download failed")


if __name__ == "__main__":
    demo()
