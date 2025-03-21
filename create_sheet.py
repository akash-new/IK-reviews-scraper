#!/usr/bin/env python3
"""
Create the IK_Reviews sheet in an existing Google Sheets document.

This script will add a sheet named "IK_Reviews" to the Google Sheets document 
specified in the storage configuration.
"""

import logging
import json
import os
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import required Google libraries
try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    google_libraries_available = True
except ImportError:
    logger.error("Google API libraries not installed")
    logger.info("To enable storage, install required packages: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    google_libraries_available = False

# Import configuration if available
try:
    from config.storage_config import StorageConfig
    config_available = True
except ImportError:
    logger.error("Failed to import StorageConfig. Make sure you're running from the project root.")
    config_available = False


def create_ik_reviews_sheet(spreadsheet_id: str, credentials_path: str) -> bool:
    """
    Create the IK_Reviews sheet in the specified spreadsheet.
    
    Args:
        spreadsheet_id: The ID of the Google Sheets document
        credentials_path: Path to the Google service account credentials file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not google_libraries_available:
        logger.error("Google API libraries not installed")
        return False
    
    try:
        # Create credentials and build service
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        sheets_service = build('sheets', 'v4', credentials=credentials)
        
        # First, check if the sheet already exists
        sheet_metadata = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        sheets = sheet_metadata.get('sheets', [])
        for sheet in sheets:
            if sheet['properties']['title'] == "IK_Reviews":
                logger.info("Sheet 'IK_Reviews' already exists")
                return True
        
        # If sheet doesn't exist, create it
        requests = [{
            'addSheet': {
                'properties': {
                    'title': 'IK_Reviews'
                }
            }
        }]
        
        body = {'requests': requests}
        response = sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
        logger.info("Successfully created sheet 'IK_Reviews'")
        return True
        
    except Exception as e:
        logger.error(f"Error creating IK_Reviews sheet: {e}")
        return False


def main():
    """Main function to create the IK_Reviews sheet."""
    if not google_libraries_available:
        return
    
    # Get configuration
    if config_available:
        config = StorageConfig()
        spreadsheet_id = config.google_sheets.get("spreadsheet_id", "")
        credentials_path = config.google_sheets.get("credentials_path", "credentials/google_sheets_credentials.json")
    else:
        # Fallback to direct reading of the storage config file
        try:
            with open("config/storage_config.json", 'r') as f:
                config_data = json.load(f)
                spreadsheet_id = config_data.get("google_sheets", {}).get("spreadsheet_id", "")
                credentials_path = config_data.get("google_sheets", {}).get("credentials_path", "credentials/google_sheets_credentials.json")
        except Exception as e:
            logger.error(f"Failed to read configuration: {e}")
            return
    
    if not spreadsheet_id:
        logger.error("No spreadsheet ID found in configuration")
        return
    
    if not os.path.exists(credentials_path):
        logger.error(f"Credentials file not found: {credentials_path}")
        return
    
    logger.info(f"Creating 'IK_Reviews' sheet in spreadsheet: {spreadsheet_id}")
    if create_ik_reviews_sheet(spreadsheet_id, credentials_path):
        logger.info(f"Sheet created successfully. You can now run your script with --storage")
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        logger.info(f"View your spreadsheet: {spreadsheet_url}")
    else:
        logger.error("Failed to create sheet")


if __name__ == "__main__":
    main() 