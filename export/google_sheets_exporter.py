"""
Google Sheets Exporter Module for IK Review Scraper.

This module provides functionality to export review data to Google Sheets.
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Basic logging setup
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GoogleSheetsExporter:
    """Handles exporting review data to Google Sheets."""
    
    def __init__(self):
        """Initialize the Google Sheets exporter."""
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        self.spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        
        if not self.credentials_path or not self.spreadsheet_id:
            raise ValueError("Missing required Google Sheets configuration")
        
        # Load credentials
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.service = build('sheets', 'v4', credentials=self.credentials)
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {str(e)}")
            raise
    
    def _get_sheet_id(self, sheet_name: str) -> int:
        """
        Get the sheet ID for a given sheet name.
        
        Args:
            sheet_name (str): Name of the sheet.
            
        Returns:
            int: Sheet ID if found, None otherwise.
        """
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            return None
            
        except HttpError as e:
            logger.error(f"Failed to get sheet ID: {str(e)}")
            return None
    
    def _create_sheet(self, sheet_name: str) -> bool:
        """
        Create a new sheet with the given name.
        
        Args:
            sheet_name (str): Name for the new sheet.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            return True
            
        except HttpError as e:
            logger.error(f"Failed to create sheet: {str(e)}")
            return False
    
    def _format_sheet(self, sheet_id: int):
        """
        Format the sheet with headers and styling.
        
        Args:
            sheet_id (int): ID of the sheet to format.
        """
        try:
            requests = [
                # Format header row
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                                'textFormat': {'bold': True},
                                'horizontalAlignment': 'CENTER',
                                'verticalAlignment': 'MIDDLE'
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
                    }
                },
                # Freeze header row
                {
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': sheet_id,
                            'gridProperties': {
                                'frozenRowCount': 1
                            }
                        },
                        'fields': 'gridProperties.frozenRowCount'
                    }
                },
                # Auto-resize columns
                {
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 12
                        }
                    }
                }
            ]
            
            body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
        except HttpError as e:
            logger.error(f"Failed to format sheet: {str(e)}")
    
    def export_reviews(self, reviews: List[Dict[str, Any]], platform: str) -> bool:
        """
        Export reviews to Google Sheets.
        
        Args:
            reviews (List[Dict[str, Any]]): List of reviews to export.
            platform (str): Platform name for the sheet.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Prepare sheet
            sheet_name = platform.replace(" ", "_")
            sheet_id = self._get_sheet_id(sheet_name)
            
            if not sheet_id:
                if not self._create_sheet(sheet_name):
                    return False
                sheet_id = self._get_sheet_id(sheet_name)
            
            # Prepare headers based on review fields
            headers = [
                "Reviewer Name", "Review Date", "Rating", "Title",
                "Review Content", "Sentiment Score", "Sentiment Category",
                "Last Updated", "Platform"
            ]
            
            # Add platform-specific headers
            if platform == "Course Report":
                headers.extend([
                    "Reviewer Description",
                    "Overall Experience Rating",
                    "Instructor Rating",
                    "Curriculum Rating",
                    "Job Assistance Rating"
                ])
            
            # Prepare data rows
            rows = [headers]
            for review in reviews:
                row = [
                    review.get("reviewer_name", ""),
                    review.get("review_date", ""),
                    review.get("rating", review.get("overall_experience_rating", "")),
                    review.get("review_title", ""),
                    review.get("review_content", ""),
                    review.get("sentiment_score", ""),
                    review.get("sentiment_category", ""),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    platform
                ]
                
                # Add platform-specific fields
                if platform == "Course Report":
                    row.extend([
                        review.get("reviewer_description", ""),
                        review.get("overall_experience_rating", ""),
                        review.get("instructor_rating", ""),
                        review.get("curriculum_rating", ""),
                        review.get("job_assistance_rating", "")
                    ])
                
                rows.append(row)
            
            # Clear existing content
            range_name = f"{sheet_name}!A1:O1000"
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            # Write new data
            body = {'values': rows}
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Format sheet
            self._format_sheet(sheet_id)
            
            logger.info(f"Successfully exported {len(reviews)} reviews to {sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export reviews: {str(e)}")
            return False


if __name__ == "__main__":
    """
    Test the Google Sheets exporter with sample data.
    
    Usage:
        python -m export.google_sheets_exporter
    """
    try:
        # Test with sample data
        print("Testing Google Sheets exporter...")
        
        # Initialize exporter
        exporter = GoogleSheetsExporter()
        
        # Load sample Trustpilot reviews
        trustpilot_reviews = []
        try:
            with open("trustpilot_reviews.json", "r") as f:
                trustpilot_reviews = json.load(f)
                print(f"Loaded {len(trustpilot_reviews)} Trustpilot reviews")
        except FileNotFoundError:
            print("No Trustpilot reviews found, skipping")
        
        # Load sample Course Report reviews
        course_report_reviews = []
        try:
            with open("course_report_reviews.json", "r") as f:
                course_report_reviews = json.load(f)
                print(f"Loaded {len(course_report_reviews)} Course Report reviews")
        except FileNotFoundError:
            print("No Course Report reviews found, skipping")
        
        # Export to Google Sheets
        success = exporter.export_reviews(
            trustpilot_reviews=trustpilot_reviews,
            platform="Trustpilot"
        )
        
        success = success and exporter.export_reviews(
            course_report_reviews=course_report_reviews,
            platform="Course Report"
        )
        
        if success:
            print("Export to Google Sheets successful!")
        else:
            print("Export to Google Sheets failed.")
        
    except Exception as e:
        print(f"Error: {str(e)}") 