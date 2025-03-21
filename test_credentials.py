#!/usr/bin/env python3
"""
Test script for verifying Google Sheets credentials.

This script validates the Google Sheets credentials file without
attempting to store any data. It's useful for troubleshooting
credential issues.
"""

import json
import logging
import os
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Try to import Google libraries
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    google_libraries_available = True
except ImportError:
    logger.error("Google API libraries not installed")
    logger.info("To enable storage, install required packages: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    google_libraries_available = False


def validate_json_format(file_path: str) -> bool:
    """Validate that the file contains valid JSON.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        True if valid JSON, False otherwise
    """
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return False


def validate_credentials_content(file_path: str) -> bool:
    """Validate that the credentials file contains required fields.
    
    Args:
        file_path: Path to the credentials file
        
    Returns:
        True if all required fields exist, False otherwise
    """
    required_fields = [
        "type", "project_id", "private_key_id", "private_key",
        "client_email", "client_id", "auth_uri", "token_uri"
    ]
    
    try:
        with open(file_path, 'r') as f:
            creds_data = json.load(f)
        
        missing_fields = [field for field in required_fields if field not in creds_data]
        
        if missing_fields:
            logger.error(f"Missing required fields: {', '.join(missing_fields)}")
            return False
        
        # Check if any fields contain placeholder values
        placeholder_values = ["YOUR_", "your-", "..."]
        for field, value in creds_data.items():
            if isinstance(value, str):
                if any(placeholder in value for placeholder in placeholder_values):
                    logger.error(f"Field '{field}' contains a placeholder value")
                    return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating credentials content: {e}")
        return False


def test_google_auth(file_path: str) -> bool:
    """Test authentication with Google using the credentials.
    
    Args:
        file_path: Path to the credentials file
        
    Returns:
        True if authentication succeeded, False otherwise
    """
    if not google_libraries_available:
        return False
        
    try:
        # Create credentials
        credentials = service_account.Credentials.from_service_account_file(
            file_path, 
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Test building the sheets service
        service = build('sheets', 'v4', credentials=credentials)
        
        # If we got here, authentication worked
        return True
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return False


def main():
    """Main function to test Google Sheets credentials."""
    credentials_path = "credentials/google_sheets_credentials.json"
    
    # Check if the credentials file exists
    if not os.path.exists(credentials_path):
        logger.error(f"Credentials file not found: {credentials_path}")
        logger.info("Please make sure the credentials file exists")
        return
    
    logger.info(f"Testing credentials file: {credentials_path}")
    
    # Step 1: Validate JSON format
    logger.info("Validating JSON format...")
    if not validate_json_format(credentials_path):
        logger.error("JSON format validation failed")
        return
    logger.info("JSON format is valid")
    
    # Step 2: Validate credentials content
    logger.info("Validating credentials content...")
    if not validate_credentials_content(credentials_path):
        logger.error("Credentials content validation failed")
        logger.info("Please update credentials file with actual values")
        return
    logger.info("Credentials content appears valid")
    
    # Step 3: Test Google authentication
    if google_libraries_available:
        logger.info("Testing Google authentication...")
        if test_google_auth(credentials_path):
            logger.info("Authentication successful! Your credentials are valid.")
        else:
            logger.error("Authentication failed")
            logger.info("Please check your credentials and make sure they have the correct permissions")
    
    # If we got here with no errors, all checks passed
    if google_libraries_available:
        logger.info("All credential checks passed")
    else:
        logger.warning("JSON format and content are valid, but Google libraries are not installed")
        logger.info("Install the required packages to complete validation")


if __name__ == "__main__":
    main() 