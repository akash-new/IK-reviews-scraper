"""
Sentiment Configuration Module for IK Review Scraper.

This module provides configuration for the sentiment analysis module,
including API selection, thresholds, and other settings.
"""

import json
import logging
import os
from typing import Dict, Any

# Basic logging setup
logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_PATH = "config/sentiment_config.json"


class SentimentConfig:
    """
    Manages configuration for the sentiment analysis module.
    
    Handles loading, saving, and providing access to sentiment analysis settings.
    """
    
    @classmethod
    def load(cls, config_path: str = DEFAULT_CONFIG_PATH) -> 'SentimentConfig':
        """
        Load a SentimentConfig instance from a config file.
        
        Args:
            config_path (str, optional): Path to the sentiment configuration JSON file.
                Defaults to 'config/sentiment_config.json'.
                
        Returns:
            SentimentConfig: A new SentimentConfig instance.
        """
        return cls(config_path)
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """
        Initialize the SentimentConfig with an optional path to the config file.
        
        Args:
            config_path (str, optional): Path to the sentiment configuration JSON file.
                Defaults to 'config/sentiment_config.json'.
        """
        self.config_path = config_path
        self.config = self._load_default_config()
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            "score_ranges": {
                "negative": (0, 49),
                "neutral": (50, 79),
                "positive": (80, 100)
            },
            "cache_results": True,
            "batch_size": 10,
            "batch_delay": 1.0
        }
    
    def save_config(self) -> None:
        """Save configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # Use default config if file doesn't exist
            self.config = self._load_default_config()
            # Save default config
            self.save_config()
    
    def get_category(self, score: int) -> str:
        """
        Get sentiment category based on score.
        
        Args:
            score (int): Sentiment score (0-100).
            
        Returns:
            str: Category ("negative", "neutral", or "positive").
        """
        ranges = self.config["score_ranges"]
        
        if score < ranges["neutral"][0]:
            return "negative"
        elif score < ranges["positive"][0]:
            return "neutral"
        else:
            return "positive"


# Create a default instance for easy import
default_config = SentimentConfig()

if __name__ == "__main__":
    # Test the SentimentConfig when run directly
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    print("Testing SentimentConfig Module")
    
    # Load the config
    config = SentimentConfig()
    
    # Print current settings
    print(f"Sentiment Analysis Enabled: {config.is_enabled}")
    print(f"Use Gemini API: {config.use_gemini}")
    print(f"Force Gemini API: {config.force_gemini}")
    print(f"Cache Results: {config.cache_results}")
    print(f"Batch Size: {config.batch_size}")
    print(f"Batch Delay: {config.batch_delay}s")
    print(f"Retry Settings: {config.retry_settings}")
    print(f"Thresholds: {config.thresholds}")
    
    # Test category function
    print(f"Score 20 -> {config.get_category(20)}")
    print(f"Score 50 -> {config.get_category(50)}")
    print(f"Score 85 -> {config.get_category(85)}")
    
    # Test setting changes
    print("\nChanging settings...")
    config.is_enabled = False
    config.batch_size = 20
    
    # Save config
    config.save_config()
    
    # Reload config to verify changes persist
    print("\nReloading config...")
    config = SentimentConfig()
    
    # Print new settings
    print(f"Sentiment Analysis Enabled: {config.is_enabled}")
    print(f"Batch Size: {config.batch_size}") 