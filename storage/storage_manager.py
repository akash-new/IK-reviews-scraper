import logging
import json
from typing import Dict, List, Any, Optional, Type

from .storage_interface import StorageInterface
from .google_sheets_storage import GoogleSheetsStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StorageManager:
    """Manager class to handle different storage implementations."""
    
    def __init__(self, config=None):
        """Initialize the storage manager.
        
        Args:
            config: Storage configuration object or dictionary.
        """
        # Handle different config formats
        if config is None:
            # Load default config
            try:
                with open('config/storage_config.json', 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load storage config: {e}")
                self.config = {"google_sheets": {"enabled": False}}
        elif hasattr(config, 'get_storage_config'):
            # Handle the StorageConfig object
            self.config = config.get_storage_config()
        elif isinstance(config, dict):
            # Use the provided dictionary directly
            self.config = config
        else:
            # Legacy handling
            try:
                self.config = config.to_dict()
            except AttributeError:
                logger.error("Invalid config format. Using default empty config.")
                self.config = {"google_sheets": {"enabled": False}}
                
        self.storage_providers = {}
        self._initialize_storage_providers()
    
    def _initialize_storage_providers(self) -> None:
        """Initialize storage provider instances."""
        # Currently, just Google Sheets is implemented
        # In the future, more providers can be added here
        if self.is_storage_enabled():
            if 'google_sheets' in self.config and self.config['google_sheets'].get('enabled', False):
                self.storage_providers["google_sheets"] = GoogleSheetsStorage(self.config['google_sheets'])
    
    def is_storage_enabled(self) -> bool:
        """Check if any storage is enabled in the configuration.
        
        Returns:
            bool: True if any storage is enabled, False otherwise.
        """
        # First check for enabled flag at top level 
        if self.config.get('enabled', False):
            return True
            
        # Then check individual providers
        if 'google_sheets' in self.config and self.config['google_sheets'].get('enabled', False):
            return True
            
        return False
    
    def store_reviews(self, reviews: List[Dict[str, Any]]) -> bool:
        """Store reviews using configured storage providers.
        
        Args:
            reviews: List of review dictionaries to store.
            
        Returns:
            bool: True if storage successful in all enabled providers, False otherwise.
        """
        if not self.is_storage_enabled():
            logger.info("Storage is disabled. Skipping storage.")
            return True
        
        if not reviews:
            logger.warning("No reviews to store.")
            return True
        
        success = True
        
        # Currently only Google Sheets is supported
        sheets_storage = self.storage_providers.get("google_sheets")
        
        if sheets_storage:
            if sheets_storage.connect():
                logger.info(f"Storing {len(reviews)} reviews in Google Sheets...")
                
                try:
                    sheets_storage.store_reviews(reviews)
                    logger.info(f"Successfully stored {len(reviews)} reviews in Google Sheets.")
                except Exception as e:
                    logger.error(f"Failed to store reviews in Google Sheets: {e}")
                    success = False
                
                sheets_storage.disconnect()
            else:
                logger.error("Failed to connect to Google Sheets. Check credentials and configuration.")
                success = False
        
        return success
    
    def get_credentials_status(self) -> Dict[str, bool]:
        """Get the status of credentials for each storage provider.
        
        Returns:
            Dictionary with storage provider names as keys and credential status as values.
        """
        status = {}
        
        # Check Google Sheets credentials
        sheets_storage = self.storage_providers.get("google_sheets")
        if sheets_storage:
            status["google_sheets"] = sheets_storage.has_valid_credentials()
        else:
            status["google_sheets"] = False
        
        return status
    
    def get_spreadsheet_url(self) -> Optional[str]:
        """Get the URL to the Google Spreadsheet if available.
        
        Returns:
            URL string or None if not available.
        """
        sheets_storage = self.storage_providers.get("google_sheets")
        if sheets_storage and sheets_storage.spreadsheet_id:
            spreadsheet_id = sheets_storage.spreadsheet_id
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        
        return None 