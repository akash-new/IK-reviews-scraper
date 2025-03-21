import json
import os
import logging
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageConfig:
    """Configuration for storage options."""

    DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "storage_config.json")
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """Initialize the storage configuration.
        
        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = config_path
        self.enabled = False
        self.google_sheets = {
            "enabled": True,
            "credentials_path": "credentials/google_sheets_credentials.json",
            "spreadsheet_id": "",
            "create_if_missing": True,
            "sheet_name": "IK_Reviews",
            "columns": [
                "s_no",
                "platform", 
                "review_date", 
                "rating", 
                "content", 
                "reviewer_name", 
                "sentiment_score", 
                "sentiment_category"
            ],
            "format_by_sentiment": True,
            "create_dashboard": True,
            "incremental_updates": True,
            "error_handling": {
                "max_retries": 3,
                "retry_delay": 5,
                "log_errors": True
            },
            "dashboard_options": {
                "show_platform_distribution": True,
                "show_sentiment_distribution": True,
                "show_score_histogram": True,
                "add_color_legend": True
            }
        }
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from the JSON file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                logger.info(f"Loading storage configuration from {self.config_path}")
                self.enabled = config.get("enabled", False)
                
                if "google_sheets" in config:
                    # Deep merge of config to preserve nested dicts
                    self._deep_merge(self.google_sheets, config["google_sheets"])
            else:
                logger.warning(f"Storage configuration file {self.config_path} not found. Using defaults.")
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading storage configuration: {e}")
            
    def _deep_merge(self, target: dict, source: dict) -> None:
        """Deep merge source dict into target dict, preserving nested structures.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # If both are dicts, recursively merge
                self._deep_merge(target[key], value)
            else:
                # Otherwise just update the value
                target[key] = value
            
    def save_config(self) -> None:
        """Save configuration to the JSON file."""
        try:
            config = {
                "enabled": self.enabled,
                "google_sheets": self.google_sheets
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved storage configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving storage configuration: {e}")
    
    def is_storage_enabled(self) -> bool:
        """Check if storage is enabled."""
        return self.enabled
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get the complete storage configuration.
        
        Returns:
            Dict containing the entire storage configuration
        """
        return {
            "enabled": self.enabled,
            "google_sheets": self.google_sheets
        }
    
    def get_google_sheets_config(self) -> Dict[str, Any]:
        """Get Google Sheets configuration."""
        return self.google_sheets
    
    def has_valid_credentials(self) -> bool:
        """Check if Google Sheets credentials exist."""
        creds_path = self.google_sheets.get("credentials_path", "")
        return os.path.exists(creds_path) if creds_path else False
    
    def has_spreadsheet_id(self) -> bool:
        """Check if a spreadsheet ID is configured."""
        return bool(self.google_sheets.get("spreadsheet_id", ""))
    
    def get_columns(self) -> List[str]:
        """Get the configured columns for the spreadsheet."""
        return self.google_sheets.get("columns", [])
    
    def set_spreadsheet_id(self, spreadsheet_id: str) -> None:
        """Set the spreadsheet ID and save the configuration.
        
        Args:
            spreadsheet_id: The ID of the Google Sheet.
        """
        self.google_sheets["spreadsheet_id"] = spreadsheet_id
        self.save_config()

# Test the configuration module if run directly
if __name__ == "__main__":
    config = StorageConfig()
    print(f"Storage enabled: {config.is_storage_enabled()}")
    print(f"Google Sheets config: {config.get_google_sheets_config()}")
    print(f"Has valid credentials: {config.has_valid_credentials()}")
    print(f"Has spreadsheet ID: {config.has_spreadsheet_id()}")
    print(f"Columns: {config.get_columns()}")
    
    # Test updating config
    if not config.has_spreadsheet_id():
        test_id = "1exampleSpreadsheetId123456789"
        config.set_spreadsheet_id(test_id)
        print(f"Updated spreadsheet ID to: {config.google_sheets['spreadsheet_id']}")
        
        # Reset for testing purposes
        config.set_spreadsheet_id("")
        print(f"Reset spreadsheet ID: {config.google_sheets['spreadsheet_id']}") 