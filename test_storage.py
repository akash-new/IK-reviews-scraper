#!/usr/bin/env python3
"""
Test script for the storage module.

This script demonstrates the functionality of the storage module
by loading sample reviews and storing them in Google Sheets.
"""

import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional

from config.storage_config import StorageConfig
from storage.storage_manager import StorageManager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_sample_reviews() -> List[Dict[str, Any]]:
    """Load sample reviews for testing.
    
    Returns:
        List of sample review dictionaries.
    """
    # First, try to load from reviews_analyzed.json if it exists
    if os.path.exists("reviews_analyzed.json"):
        try:
            with open("reviews_analyzed.json", "r") as f:
                reviews = json.load(f)
                if reviews:
                    logger.info(f"Loaded {len(reviews)} reviews from reviews_analyzed.json")
                    return reviews
        except Exception as e:
            logger.error(f"Error loading reviews from file: {e}")
    
    # If no file exists or it's empty, use sample data
    logger.info("Using sample review data")
    return [
        {
            "platform": "Trustpilot",
            "reviewer_name": "John Smith",
            "review_date": "2023-01-15",
            "rating": "5/5",
            "content": "Interview Kickstart was an amazing experience. The instructors were knowledgeable and the curriculum was comprehensive. I received multiple job offers after completing the program.",
            "relevant": True,
            "sentiment_score": 90,
            "sentiment_category": "POSITIVE"
        },
        {
            "platform": "Course Report",
            "reviewer_name": "Jane Doe",
            "review_date": "2022-11-20",
            "rating": "3/5",
            "content": "The course was okay. Some instructors were great, others not so much. The mock interviews were helpful but I wish there were more of them. The content was sometimes outdated.",
            "relevant": True,
            "sentiment_score": 60,
            "sentiment_category": "NEUTRAL"
        },
        {
            "platform": "Trustpilot",
            "reviewer_name": "Alice Johnson",
            "review_date": "2023-02-10",
            "rating": "1/5",
            "content": "Waste of money. The content was outdated and not helpful for interviews. The instructors were often late or unprepared. I did not get value for the high price I paid.",
            "relevant": True,
            "sentiment_score": 20,
            "sentiment_category": "NEGATIVE"
        },
        {
            "platform": "Reddit",
            "reviewer_name": "tech_enthusiast",
            "review_date": "2023-03-05",
            "rating": "4/5",
            "content": "I found Interview Kickstart to be quite helpful in my job search. The system design module was excellent and exactly what I needed to level up in my interviews.",
            "relevant": True,
            "sentiment_score": 85,
            "sentiment_category": "POSITIVE"
        },
        {
            "platform": "Quora",
            "reviewer_name": "Anonymous User",
            "review_date": "2022-12-15",
            "rating": "2/5",
            "content": "Not worth the high price. While some content was useful, most of it could be found for free online. The instructors were knowledgeable but the course structure was disorganized.",
            "relevant": True,
            "sentiment_score": 40,
            "sentiment_category": "NEGATIVE"
        }
    ]


def main():
    """Main function to test the storage module."""
    # Load the storage configuration
    storage_config = StorageConfig()
    logger.info(f"Loaded storage configuration from {storage_config.config_path}")
    
    # Log configuration details
    if storage_config.is_storage_enabled():
        logger.info("Storage is enabled")
    else:
        logger.info("Storage is disabled - enabling for this test")
        storage_config.enabled = True
        storage_config.save_config()
    
    # Check credentials
    if not storage_config.has_valid_credentials():
        logger.error("Google Sheets credentials not found")
        logger.info(f"Please create a valid credentials file at: {storage_config.google_sheets['credentials_path']}")
        logger.info("You can use the template file as a reference: credentials/google_sheets_credentials_template.json")
        return
    
    # Load sample reviews
    reviews = load_sample_reviews()
    
    # Initialize storage manager
    storage_manager = StorageManager(storage_config)
    
    # Check credentials status
    credentials_status = storage_manager.get_credentials_status()
    if not credentials_status.get("google_sheets", False):
        logger.error("Google Sheets credentials are not valid")
        return
    
    # Store reviews
    logger.info(f"Storing {len(reviews)} reviews in Google Sheets...")
    if storage_manager.store_reviews(reviews):
        # Get the spreadsheet URL
        spreadsheet_url = storage_manager.get_spreadsheet_url()
        if spreadsheet_url:
            logger.info(f"Reviews stored successfully. Spreadsheet URL: {spreadsheet_url}")
        else:
            logger.info("Reviews stored successfully, but spreadsheet URL not available")
    else:
        logger.error("Failed to store reviews in Google Sheets")
    
    # Save the spreadsheet ID to the config file for future use
    sheets_storage = storage_manager.storage_providers.get("google_sheets")
    if sheets_storage and sheets_storage.spreadsheet_id:
        logger.info(f"Saving spreadsheet ID to configuration: {sheets_storage.spreadsheet_id}")
        storage_config.set_spreadsheet_id(sheets_storage.spreadsheet_id)


if __name__ == "__main__":
    main() 