"""
validators.py - Input validation for Spot-Ninja

Validates:
- Latitude/longitude bounds (within Canada, HRDPS domain)
- DEM resolution availability
- Weather model availability
- ROI size constraints
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Canada bounding box (approximate)
CANADA_BOUNDS = {
    "min_lat": 41.7,   # Southern Canada
    "max_lat": 83.1,   # Arctic
    "min_lon": -141.0, # Western Canada
    "max_lon": -52.6   # Eastern Canada
}

# HRDPS Continental Domain (2.5km resolution)
# Covers most of Canada; higher resolution (1km) available in limited areas
HRDPS_BOUNDS = {
    "min_lat": 40.0,
    "max_lat": 60.0,
    "min_lon": -141.0,
    "max_lon": -40.0
}

# GDPS domain (10km global coverage)
GDPS_BOUNDS = {
    "min_lat": -90.0,
    "max_lat": 90.0,
    "min_lon": -180.0,
    "max_lon": 180.0
}

# CanElevation DEM collections and their resolutions
CANELEVATION_COLLECTIONS = {
    "hrdem-mosaic-1m": {"resolution": 1, "coverage": "nationwide", "preferred": True},
    "hrdem-mosaic-2m": {"resolution": 2, "coverage": "nationwide", "preferred": False},
    "mrdem-30": {"resolution": 30, "coverage": "nationwide (complete)", "preferred": False},
    "hrdem-lidar": {"resolution": "variable", "coverage": "LiDAR project areas", "preferred": False},
    "hrdem-arcticdem": {"resolution": 2, "coverage": "Northern Canada", "preferred": False},
}

# Valid resolution options for DEM selection
VALID_DEM_RESOLUTIONS = ["1m", "2m", "30m"]

# Valid output formats
VALID_OUTPUT_FORMATS = ["kmz", "geotiff"]


def validate_coordinates(latitude: float, longitude: float, strict: bool = True) -> Tuple[bool, str]:
    """
    Validate latitude and longitude are within Canada/HRDPS domain.

    Args:
        latitude (float): Latitude (-90 to 90)
        longitude (float): Longitude (-180 to 180)
        strict (bool): If True, require HRDPS domain; if False, allow Canada bounds

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Check basic bounds
    if not (-90 <= latitude <= 90):
        return False, f"Latitude {latitude} out of range [-90, 90]"
    if not (-180 <= longitude <= 180):
        return False, f"Longitude {longitude} out of range [-180, 180]"

    # Check Canada bounds (relaxed)
    if not (CANADA_BOUNDS["min_lat"] <= latitude <= CANADA_BOUNDS["max_lat"]):
        return False, f"Latitude {latitude} outside Canada bounds [{CANADA_BOUNDS['min_lat']}, {CANADA_BOUNDS['max_lat']}]"
    if not (CANADA_BOUNDS["min_lon"] <= longitude <= CANADA_BOUNDS["max_lon"]):
        return False, f"Longitude {longitude} outside Canada bounds [{CANADA_BOUNDS['min_lon']}, {CANADA_BOUNDS['max_lon']}]"

    # Check HRDPS domain (stricter)
    if strict:
        if not (HRDPS_BOUNDS["min_lat"] <= latitude <= HRDPS_BOUNDS["max_lat"]):
            return False, f"Latitude {latitude} outside HRDPS domain [{HRDPS_BOUNDS['min_lat']}, {HRDPS_BOUNDS['max_lat']}]. GDPS fallback available."
        if not (HRDPS_BOUNDS["min_lon"] <= longitude <= HRDPS_BOUNDS["max_lon"]):
            return False, f"Longitude {longitude} outside HRDPS domain [{HRDPS_BOUNDS['min_lon']}, {HRDPS_BOUNDS['max_lon']}]. GDPS fallback available."

    return True, ""


def validate_roi_size(roi_km: float) -> Tuple[bool, str]:
    """
    Validate Region of Interest size.

    Args:
        roi_km (float): ROI size in km

    Returns:
        Tuple[bool, str]: (is_valid, warning_or_error_message)
    """
    if roi_km <= 0:
        return False, f"ROI size must be positive, got {roi_km} km"
    if roi_km < 2:
        return False, f"ROI size {roi_km} km is too small; minimum 2 km"
    if roi_km > 50:
        return False, f"ROI size {roi_km} km is very large; maximum recommended 50 km (may impact performance)"
    
    return True, ""


def validate_dem_collection(collection: str) -> Tuple[bool, str]:
    """
    Validate DEM collection name.

    Args:
        collection (str): CanElevation collection name

    Returns:
        Tuple[bool, str]: (is_valid, error_or_warning_message)
    """
    if collection not in CANELEVATION_COLLECTIONS:
        available = ", ".join(CANELEVATION_COLLECTIONS.keys())
        return False, f"Unknown collection '{collection}'. Available: {available}"

    if not CANELEVATION_COLLECTIONS[collection]["preferred"]:
        logger.warning(f"Collection '{collection}' is not preferred. Consider using 'hrdem-mosaic-1m' for best quality.")

    return True, ""


def validate_dem_resolution(resolution: str) -> Tuple[bool, str]:
    """
    Validate DEM resolution option.

    Args:
        resolution (str): Resolution string ("1m", "2m", or "30m")

    Returns:
        Tuple[bool, str]: (is_valid, error_or_warning_message)
    """
    if resolution not in VALID_DEM_RESOLUTIONS:
        return False, f"Invalid resolution '{resolution}'. Valid: {', '.join(VALID_DEM_RESOLUTIONS)}"

    return True, ""


def validate_weather_model(model: str, resolution: str) -> Tuple[bool, str]:
    """
    Validate weather model and resolution combination.

    Args:
        model (str): Model name ("HRDPS" or "GDPS")
        resolution (str): Resolution ("1.0km", "2.5km", "10km", etc.)

    Returns:
        Tuple[bool, str]: (is_valid, error_or_warning_message)
    """
    valid_models = {
        "HRDPS": ["1.0km", "2.5km"],
        "GDPS": ["10km"],
    }

    if model not in valid_models:
        available = ", ".join(valid_models.keys())
        return False, f"Unknown model '{model}'. Valid: {available}"

    if resolution not in valid_models[model]:
        valid_resolutions = ", ".join(valid_models[model])
        return False, f"Invalid resolution '{resolution}' for model '{model}'. Valid: {valid_resolutions}"

    return True, ""


def validate_output_format(format_str: str) -> Tuple[bool, str]:
    """
    Validate output format.

    Args:
        format_str (str): Output format ("kmz" or "geotiff")

    Returns:
        Tuple[bool, str]: (is_valid, error_or_warning_message)
    """
    if format_str not in VALID_OUTPUT_FORMATS:
        return False, f"Invalid format '{format_str}'. Valid: {', '.join(VALID_OUTPUT_FORMATS)}"

    return True, ""


def validate_all(latitude: float, longitude: float, roi_km: float, 
                 dem_collection: str, model: str, resolution: str) -> dict:
    """
    Validate all input parameters together.

    Args:
        latitude (float): Latitude
        longitude (float): Longitude
        roi_km (float): ROI size in km
        dem_collection (str): CanElevation collection
        model (str): Weather model
        resolution (str): Model resolution

    Returns:
        dict: {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str]
        }
    """
    result = {"valid": True, "errors": [], "warnings": []}

    # Validate coordinates
    is_valid, msg = validate_coordinates(latitude, longitude)
    if not is_valid:
        result["valid"] = False
        result["errors"].append(msg)

    # Validate ROI
    is_valid, msg = validate_roi_size(roi_km)
    if not is_valid:
        result["valid"] = False
        result["errors"].append(msg)

    # Validate DEM
    is_valid, msg = validate_dem_collection(dem_collection)
    if not is_valid:
        result["valid"] = False
        result["errors"].append(msg)

    # Validate weather model
    is_valid, msg = validate_weather_model(model, resolution)
    if not is_valid:
        result["valid"] = False
        result["errors"].append(msg)

    return result
