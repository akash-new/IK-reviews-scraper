"""
Filter Configuration Module for IK Review Scraper.

This module provides configuration for the relevance filtering module,
including which platforms to filter and default filter settings.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional, Set

# Basic logging setup
logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_PATH = "config/filter_config.json"


class FilterConfig:
    """
    Manages configuration for the relevance filtering module.
    
    Handles loading, saving, and providing access to filter settings such as
    which platforms to apply filtering to.
    """
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """
        Initialize the FilterConfig with an optional path to the config file.
        
        Args:
            config_path (str, optional): Path to the filter configuration JSON file.
                Defaults to 'config/filter_config.json'.
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the JSON file. If file doesn't exist, create a default config.
        
        Returns:
            Dict[str, Any]: The loaded configuration.
        """
        # Default configuration
        default_config = {
            "enabled": True,  # Whether filtering is enabled by default
            "platforms_to_filter": [],  # Empty list means filter all platforms
            "filter_all_platforms": True,  # Whether to filter all platforms by default
        }
        
        # Try to load from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded filter configuration from {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"Failed to load filter config: {str(e)}")
                logger.info("Using default filter configuration")
                return default_config
        else:
            # Create default config file
            logger.info(f"Filter config file not found. Creating default config at {self.config_path}")
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            try:
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to create default config file: {str(e)}")
            
            return default_config
    
    def save_config(self) -> bool:
        """
        Save the current configuration to the JSON file.
        
        Returns:
            bool: True if save was successful, False otherwise.
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved filter configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save filter config: {str(e)}")
            return False
    
    @property
    def is_enabled(self) -> bool:
        """
        Check if filtering is enabled.
        
        Returns:
            bool: True if filtering is enabled, False otherwise.
        """
        return self.config.get("enabled", True)
    
    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        """
        Set whether filtering is enabled.
        
        Args:
            value (bool): True to enable filtering, False to disable.
        """
        self.config["enabled"] = bool(value)
    
    @property
    def filter_all_platforms(self) -> bool:
        """
        Check if all platforms should be filtered.
        
        Returns:
            bool: True if all platforms should be filtered, False if only specific platforms.
        """
        return self.config.get("filter_all_platforms", True)
    
    @filter_all_platforms.setter
    def filter_all_platforms(self, value: bool) -> None:
        """
        Set whether all platforms should be filtered.
        
        Args:
            value (bool): True to filter all platforms, False to filter only specific platforms.
        """
        self.config["filter_all_platforms"] = bool(value)
    
    @property
    def platforms_to_filter(self) -> List[str]:
        """
        Get the list of platforms to filter.
        
        Returns:
            List[str]: List of platform names to apply filtering to.
                Empty list if filter_all_platforms is True.
        """
        return self.config.get("platforms_to_filter", [])
    
    @platforms_to_filter.setter
    def platforms_to_filter(self, platforms: List[str]) -> None:
        """
        Set the list of platforms to filter.
        
        Args:
            platforms (List[str]): List of platform names to apply filtering to.
        """
        self.config["platforms_to_filter"] = list(platforms)
        
        # If platforms are specified, set filter_all_platforms to False
        if platforms:
            self.config["filter_all_platforms"] = False
    
    def get_platforms_to_filter(self) -> Optional[List[str]]:
        """
        Get the list of platforms to filter, considering the filter_all_platforms setting.
        
        Returns:
            Optional[List[str]]: List of platform names to apply filtering to, or None if all platforms.
        """
        if self.filter_all_platforms:
            return None  # None means filter all platforms
        else:
            return self.platforms_to_filter


# Create a default instance for easy import
default_config = FilterConfig()

if __name__ == "__main__":
    # Test the FilterConfig when run directly
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    print("Testing FilterConfig Module")
    
    # Load the config
    config = FilterConfig()
    
    # Print current settings
    print(f"Filtering Enabled: {config.is_enabled}")
    print(f"Filter All Platforms: {config.filter_all_platforms}")
    print(f"Platforms to Filter: {config.platforms_to_filter}")
    
    # Test setting changes
    print("\nChanging settings...")
    config.is_enabled = True
    config.filter_all_platforms = False
    config.platforms_to_filter = ["Trustpilot", "Course Report"]
    
    # Save config
    config.save_config()
    
    # Reload config to verify changes persist
    print("\nReloading config...")
    config = FilterConfig()
    
    # Print new settings
    print(f"Filtering Enabled: {config.is_enabled}")
    print(f"Filter All Platforms: {config.filter_all_platforms}")
    print(f"Platforms to Filter: {config.platforms_to_filter}")
    print(f"get_platforms_to_filter(): {config.get_platforms_to_filter()}") 