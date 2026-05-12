"""
utils.py - Utility functions for Spot-Ninja

Includes:
- Configuration loading
- Logging setup
- Common utility functions
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML required. Install: pip install PyYAML")

try:
    from dotenv import load_dotenv
except ImportError:
    raise ImportError("python-dotenv required. Install: pip install python-dotenv")


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file (Optional[Path]): Log file path; if None, logs to console only

    Returns:
        logging.Logger: Configured root logger
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")

    return logger


def load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from .env file.

    Args:
        env_path (Optional[Path]): Path to .env file; defaults to .env in current directory

    Returns:
        Dict[str, str]: Environment variables
    """
    if env_path is None:
        env_path = Path(".env")

    if env_path.exists():
        load_dotenv(env_path)
        logging.info(f"Loaded environment from {env_path}")
    else:
        logging.warning(f"Environment file not found: {env_path}")

    return dict(os.environ)


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path (Path): Path to YAML config file

    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        logging.info(f"Loaded config from {config_path}")
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}")


def get_data_paths(base_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Get standard data directory paths.

    Args:
        base_dir (Optional[Path]): Base data directory; defaults to ./data

    Returns:
        Dict[str, Path]: Dictionary of path names to paths
    """
    if base_dir is None:
        base_dir = Path("data")

    paths = {
        "base": base_dir,
        "dems": base_dir / "dems",
        "weather": base_dir / "weather",
        "output": base_dir / "output",
    }

    # Create directories if they don't exist
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    return paths


def format_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> str:
    """
    Format bounding box as readable string.

    Args:
        min_lon (float): Minimum longitude
        min_lat (float): Minimum latitude
        max_lon (float): Maximum longitude
        max_lat (float): Maximum latitude

    Returns:
        str: Formatted string
    """
    return f"lat [{min_lat:.4f}, {max_lat:.4f}], lon [{min_lon:.4f}, {max_lon:.4f}]"


class Config:
    """Configuration manager for Spot-Ninja."""

    def __init__(self, config_path: Path, env_path: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path (Path): Path to YAML config file
            env_path (Optional[Path]): Path to .env file
        """
        self.config_path = config_path
        self.env_path = env_path or Path(".env")

        # Load files
        load_env_file(self.env_path)
        self.config = load_config(self.config_path)

        self.logger = logging.getLogger(__name__)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key (str): Dot-separated key (e.g., "location.latitude")
            default (Any): Default if not found

        Returns:
            Any: Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def location(self) -> tuple:
        """Get location (latitude, longitude)."""
        return (
            self.get("location.latitude"),
            self.get("location.longitude"),
        )

    def roi_size(self) -> float:
        """Get ROI size in km."""
        return self.get("roi.size_km", 10)

    def dem_config(self) -> dict:
        """Get DEM configuration."""
        return self.get("dem", {})

    def weather_config(self) -> dict:
        """Get weather configuration."""
        return self.get("weather", {})

    def windninja_config(self) -> dict:
        """Get WindNinja configuration."""
        return self.get("windninja", {})

    def output_formats(self) -> list:
        """Get output formats."""
        return self.get("windninja.output_formats", ["kmz"])

    def stability_enabled(self) -> bool:
        """Check if stability mode is enabled."""
        return self.get("windninja.stability", False)
