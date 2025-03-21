import logging
import json
import os
import time
from typing import List, Dict, Any, Optional, Tuple, Union, Set

# Google API imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    # We import the credential modules on demand in _init_services()
    google_api_available = True
except ImportError:
    google_api_available = False

from .storage_interface import StorageInterface
from .utils import format_review_for_storage, get_cell_format_for_sentiment, create_dashboard_data
from config.storage_config import StorageConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define scopes for Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Define retry parameters
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class GoogleSheetsStorage(StorageInterface):
    """Implementation of storage interface for Google Sheets."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Google Sheets storage connection.
        
        Args:
            config: Configuration dictionary with Google Sheets settings.
        """
        self.config = config
        self.sheets_service = None
        self.drive_service = None
        
        # Extract configuration values with defaults
        self.credentials_path = config.get('credentials_path', 'credentials/google_sheets_credentials.json')
        self.spreadsheet_id = config.get('spreadsheet_id', '')
        self.create_if_missing = config.get('create_if_missing', True)
        
        # Support both naming conventions for backward compatibility
        self.sheet_name = config.get('sheet_name', config.get('default_sheet_name', 'IK_Reviews'))
        
        self.columns = config.get('columns', [])
        self.format_by_sentiment = config.get('format_by_sentiment', True)
        self.create_dashboard = config.get('create_dashboard', True)
        
        # Initialize services
        self._init_services()
    
    def has_valid_credentials(self) -> bool:
        """Check if Google Sheets credentials exist and are valid.
        
        Returns:
            bool: True if credentials file exists, False otherwise.
        """
        if not os.path.exists(self.credentials_path):
            logger.error(f"Credentials file not found at {self.credentials_path}")
            return False
        
        # Basic check to see if the file contains valid JSON
        try:
            with open(self.credentials_path, 'r') as f:
                creds_data = json.load(f)
                if 'type' not in creds_data:
                    logger.error(f"Invalid credentials file format: missing 'type' field")
                    return False
                return True
        except json.JSONDecodeError:
            logger.error(f"Invalid credentials file format: not valid JSON")
            return False
        except Exception as e:
            logger.error(f"Error checking credentials: {e}")
            return False
    
    def connect(self) -> bool:
        """Connect to Google Sheets API and initialize services.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            if not self.sheets_service or not self.drive_service:
                self._init_services()
                
            # Check if the spreadsheet exists or create it if needed
            if not self.spreadsheet_id:
                if self.create_if_missing:
                    self._create_spreadsheet()
                else:
                    logger.error("No spreadsheet ID provided and create_if_missing is disabled")
                    return False
            
            # Verify we can access the spreadsheet
            try:
                sheet_metadata = self.sheets_service.spreadsheets().get(
                    spreadsheetId=self.spreadsheet_id
                ).execute()
                
                logger.info(f"Connected to Google Sheets: {sheet_metadata.get('properties', {}).get('title', 'Unknown')}")
                return True
                
            except Exception as e:
                if "Requested entity was not found" in str(e) and self.create_if_missing:
                    logger.warning(f"Spreadsheet with ID {self.spreadsheet_id} not found. Creating a new spreadsheet.")
                    self._create_spreadsheet()
                    return True
                else:
                    logger.error(f"Error accessing spreadsheet: {e}")
                    return False
            
        except Exception as e:
            logger.error(f"Error connecting to Google Sheets: {e}")
            return False
    
    def _create_spreadsheet(self) -> None:
        """Create a new Google Sheets spreadsheet."""
        try:
            # Create a new spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': 'Interview Kickstart Reviews'
                },
                'sheets': [
                    {
                        'properties': {
                            'title': self.sheet_name
                        }
                    }
                ]
            }
            
            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            self.spreadsheet_id = spreadsheet.get('spreadsheetId')
            logger.info(f"Created new spreadsheet with ID: {self.spreadsheet_id}")
            
            # Initialize the sheet with headers
            self._init_sheet_headers()
            
            # Update the spreadsheet ID in the config
            self.config['spreadsheet_id'] = self.spreadsheet_id
            
            # Save the updated config back to the file
            try:
                with open('config/storage_config.json', 'r') as f:
                    full_config = json.load(f)
                    
                full_config['google_sheets']['spreadsheet_id'] = self.spreadsheet_id
                
                with open('config/storage_config.json', 'w') as f:
                    json.dump(full_config, f, indent=2)
                    
                logger.info(f"Updated spreadsheet ID in config file")
            except Exception as e:
                logger.error(f"Error updating config file with new spreadsheet ID: {e}")
            
        except Exception as e:
            logger.error(f"Error creating spreadsheet: {e}")
    
    def _init_sheet_headers(self) -> None:
        """Initialize the sheet with headers based on configured columns."""
        try:
            # Define the header row based on configured columns
            headers = []
            column_mapping = {
                's_no': 'S.NO',
                'platform': 'PLATFORM',
                'review_date': 'REVIEW DATE',
                'rating': 'RATING',
                'content': 'REVIEW CONTENT',
                'reviewer_name': 'REVIEWER NAME',
                'sentiment_score': 'SENTIMENT SCORE',
                'sentiment_category': 'SENTIMENT CATEGORY'
            }
            
            # Create headers row using the mapping
            for column in self.columns:
                header = column_mapping.get(column, column.upper())
                headers.append(header)
                
            # Update the header row (A1:H1)
            body = {'values': [headers]}
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1",
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Format header row
            sheet_id = self._get_sheet_id(self.sheet_name)
            if sheet_id:
                requests = [{
                    'updateCells': {
                        'rows': [{
                            'values': [{
                                'userEnteredFormat': {
                                    'textFormat': {'bold': True},
                                    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                                    'horizontalAlignment': 'CENTER'
                                }
                            } for _ in range(len(headers))]
                        }],
                        'fields': 'userEnteredFormat',
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': len(headers)
                        }
                    }
                }]
                
                body = {'requests': requests}
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                
            logger.info(f"Initialized sheet headers for {self.sheet_name}")
            
        except Exception as e:
            logger.error(f"Error initializing sheet headers: {e}")
    
    def store_reviews(self, reviews: List[Dict[str, Any]]) -> None:
        """Store reviews in Google Sheets.
        
        Args:
            reviews: List of review dictionaries to store.
        """
        if not reviews:
            logger.warning("No reviews to store in Google Sheets.")
            return
        
        try:
            # Check if sheet exists and create it if needed
            sheet_id = self._get_sheet_id(self.sheet_name)
            if sheet_id is None and self.create_if_missing:
                logger.info(f"Sheet '{self.sheet_name}' not found, creating it")
                
                # Add a new sheet with the given name
                body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': self.sheet_name
                            }
                        }
                    }]
                }
                
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                
                # Get the new sheet ID
                sheet_id = self._get_sheet_id(self.sheet_name)
                if not sheet_id:
                    logger.error(f"Failed to create sheet '{self.sheet_name}'")
                    return
            
            # Initialize sheet with headers if needed
            self._init_sheet_headers()
            
            # Decide whether to use incremental updates
            incremental = self.config.get("incremental_updates", False)
            
            if incremental:
                # Perform incremental update (append only new reviews)
                self._store_reviews_incrementally(reviews)
            else:
                # Use traditional clear and re-write approach
                self._clear_data()
                self._store_all_reviews(reviews)
            
            # Apply formatting if enabled
            if self.format_by_sentiment:
                self._apply_sentiment_formatting()
            
            # Update dashboard if enabled
            if self.create_dashboard:
                # Check if dashboard exists
                dashboard_exists = False
                sheets_info = self.sheets_service.spreadsheets().get(
                    spreadsheetId=self.spreadsheet_id
                ).execute().get('sheets', [])
                
                for sheet in sheets_info:
                    if sheet.get('properties', {}).get('title') == 'Dashboard':
                        dashboard_exists = True
                        break
                
                if not dashboard_exists:
                    self._create_dashboard_sheet()
            
            logger.info(f"Successfully stored {len(reviews)} reviews in Google Sheets.")
            
        except Exception as e:
            logger.error(f"Error storing reviews in Google Sheets: {e}")
            # Attempt to recover if possible
            self._handle_storage_error(e)

    def _store_reviews_incrementally(self, new_reviews: List[Dict[str, Any]]) -> None:
        """Store reviews incrementally (append only new reviews).
        
        Args:
            new_reviews: List of new review dictionaries to append.
        """
        try:
            # Get existing review IDs to avoid duplicates
            existing_ids = self._get_existing_review_ids()
            logger.info(f"Found {len(existing_ids)} existing reviews in the sheet")
            
            # Filter out reviews that already exist in the sheet
            reviews_to_add = []
            for review in new_reviews:
                # Create a unique ID for the review based on content and platform
                review_id = self._generate_review_id(review)
                if review_id not in existing_ids:
                    reviews_to_add.append(review)
            
            logger.info(f"Adding {len(reviews_to_add)} new reviews to the sheet")
            
            if not reviews_to_add:
                logger.info("No new reviews to add")
                return
                
            # Format the new reviews for storage
            formatted_reviews = []
            for i, review in enumerate(reviews_to_add):
                # Get the next available S.NO value
                next_sno = len(existing_ids) + i + 1  # +1 because s_no starts at 1
                
                formatted_review = format_review_for_storage(review, self.columns, s_no=next_sno)
                formatted_reviews.append(formatted_review)
            
            # Append the new reviews to the sheet
            body = {'values': formatted_reviews}
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Appended {len(formatted_reviews)} new reviews to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error in incremental update: {e}")
            # Fall back to full refresh
            logger.info("Falling back to full refresh")
            self._clear_data()
            self._store_all_reviews(new_reviews)

    def _get_existing_review_ids(self) -> Set[str]:
        """Get the IDs of reviews that already exist in the sheet.
        
        Returns:
            A set of unique review IDs.
        """
        review_ids = set()
        try:
            # Retrieve all data from the sheet
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A:H"
            ).execute()
            
            values = result.get('values', [])
            
            if len(values) <= 1:  # Only the header row
                return review_ids
                
            # Skip the header row
            for row in values[1:]:
                if len(row) >= 6:  # Ensure the row has enough columns
                    # Platform is usually column B (index 1)
                    platform_index = min(1, len(row) - 1)
                    platform = row[platform_index] if platform_index < len(row) else ""
                    
                    # Content is usually column E (index 4)
                    content_index = min(4, len(row) - 1)
                    content = row[content_index] if content_index < len(row) else ""
                    
                    if platform and content:
                        review_id = self._generate_review_id({
                            "platform": platform,
                            "content": content
                        })
                        review_ids.add(review_id)
            
            return review_ids
            
        except Exception as e:
            logger.error(f"Error retrieving existing reviews: {e}")
            return set()
            
    def _generate_review_id(self, review: Dict[str, Any]) -> str:
        """Generate a unique ID for a review based on its content and platform.
        
        Args:
            review: The review dictionary.
            
        Returns:
            A unique ID string.
        """
        # Get the platform and content
        platform = review.get("platform", "")
        content = review.get("review_content", review.get("content", ""))
        
        # Use a hash of the content and platform as the ID
        # Truncate content to first 200 chars to avoid excessive processing
        content_preview = content[:200] if content else ""
        id_string = f"{platform}:{content_preview}"
        
        # Use a hash function to create a unique ID
        import hashlib
        return hashlib.md5(id_string.encode('utf-8')).hexdigest()
        
    def _store_all_reviews(self, reviews: List[Dict[str, Any]]) -> None:
        """Store all reviews in Google Sheets, replacing existing data.
        
        Args:
            reviews: List of review dictionaries to store.
        """
        # Format the reviews for storage
        formatted_reviews = []
        for i, review in enumerate(reviews):
            formatted_review = format_review_for_storage(review, self.columns, s_no=i+1)
            formatted_reviews.append(formatted_review)
        
        # Store the formatted reviews
        body = {'values': formatted_reviews}
        result = self.sheets_service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.sheet_name}!A2",
            valueInputOption='RAW',
            body=body
        ).execute()
        
        logger.info(f"Stored {len(formatted_reviews)} reviews in Google Sheets")
        
    def _handle_storage_error(self, error: Exception) -> None:
        """Handle errors during storage operations with recovery attempts.
        
        Args:
            error: The exception that occurred.
        """
        # Check for specific error types and attempt recovery
        error_message = str(error)
        
        if "Quota exceeded" in error_message:
            logger.error("Google Sheets API quota exceeded. Please try again later.")
        elif "invalid_grant" in error_message:
            logger.error("Authentication issue. Check your Google API credentials.")
        elif "Socket timeout" in error_message or "Connection reset" in error_message:
            logger.error("Network issue. Check your internet connection.")
            # Could implement retry logic here
        elif "Sheet not found" in error_message:
            logger.error("Sheet not found. Will attempt to create it on next run.")
        else:
            logger.error(f"Unhandled storage error: {error_message}")
        
        # Log additional debugging information
        import traceback
        logger.debug(f"Error traceback: {traceback.format_exc()}")
        
        # Notify about potential recovery steps
        logger.info("To recover: 1) Check your internet connection, 2) Verify Google API credentials, 3) Ensure spreadsheet exists and permissions are set correctly")
    
    def _apply_sentiment_formatting(self) -> None:
        """Apply enhanced formatting to rows based on sentiment category and score."""
        try:
            if not self.sheets_service or not self.spreadsheet_id:
                logger.error(f"Sheets service or spreadsheet ID not initialized")
                return
                
            sheet_id = self._get_sheet_id(self.sheet_name)
            if not sheet_id:
                logger.error(f"Sheet ID not found for {self.sheet_name}")
                return
            
            # Get the data to determine sentiment values for formatting
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A:H"
            ).execute()
            
            values = result.get('values', [])
            if len(values) <= 1:  # Only header row or empty
                logger.info("No data to format")
                return
                
            # Find column indices for sentiment score and category
            header_row = values[0]
            score_idx = -1
            category_idx = -1
            
            for i, header in enumerate(header_row):
                if "SCORE" in header.upper():
                    score_idx = i
                elif "CATEGORY" in header.upper():
                    category_idx = i
            
            if score_idx == -1 or category_idx == -1:
                logger.error("Could not find sentiment score or category columns")
                return
                
            # Prepare formatting requests
            requests = []
            
            # 1. Format based on sentiment category
            for row_idx in range(1, len(values)):
                if row_idx >= len(values) or category_idx >= len(values[row_idx]):
                    continue
                    
                category = values[row_idx][category_idx] if category_idx < len(values[row_idx]) else ""
                background_color = {"red": 0.95, "green": 0.95, "blue": 0.95}  # Default gray
                
                if category.upper() == "POSITIVE":
                    background_color = {"red": 0.8, "green": 1.0, "blue": 0.8}  # Light green
                elif category.upper() == "NEGATIVE":
                    background_color = {"red": 1.0, "green": 0.8, "blue": 0.8}  # Light red
                
                # Apply row formatting based on sentiment category
                requests.append({
                    'updateCells': {
                        'rows': [{
                            'values': [{'userEnteredFormat': {'backgroundColor': background_color}} 
                                     for _ in range(len(header_row))]
                        }],
                        'fields': 'userEnteredFormat.backgroundColor',
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': row_idx,
                            'endRowIndex': row_idx + 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': len(header_row)
                        }
                    }
                })
            
            # 2. Apply gradient formatting to sentiment score column
            # This creates a conditional formatting rule that colors cells based on value
            requests.append({
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{
                            'sheetId': sheet_id,
                            'startRowIndex': 1,  # Skip header
                            'startColumnIndex': score_idx,
                            'endColumnIndex': score_idx + 1
                        }],
                        'gradientRule': {
                            'minpoint': {
                                'color': {'red': 1.0, 'green': 0.4, 'blue': 0.4},
                                'type': 'NUMBER',
                                'value': '0'
                            },
                            'midpoint': {
                                'color': {'red': 1.0, 'green': 1.0, 'blue': 0.4},
                                'type': 'NUMBER',
                                'value': '50'
                            },
                            'maxpoint': {
                                'color': {'red': 0.4, 'green': 1.0, 'blue': 0.4},
                                'type': 'NUMBER',
                                'value': '100'
                            }
                        }
                    },
                    'index': 0
                }
            })
            
            # 3. Add color legend at the bottom
            # First, determine where to place the legend (after the last row)
            legend_row = len(values) + 2  # Skip a row after the data
            
            # Add a title for the legend
            requests.append({
                'updateCells': {
                    'rows': [{
                        'values': [{
                            'userEnteredValue': {'stringValue': 'SENTIMENT COLOR KEY'},
                            'userEnteredFormat': {
                                'textFormat': {'bold': True},
                                'horizontalAlignment': 'CENTER'
                            }
                        }]
                    }],
                    'fields': 'userEnteredValue,userEnteredFormat',
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': legend_row,
                        'endRowIndex': legend_row + 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 3
                    }
                }
            })
            
            # Add positive sentiment legend
            requests.append({
                'updateCells': {
                    'rows': [{
                        'values': [
                            {'userEnteredValue': {'stringValue': 'Positive'},
                             'userEnteredFormat': {'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}}},
                            {'userEnteredValue': {'stringValue': '80-100'},
                             'userEnteredFormat': {'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}}}
                        ]
                    }],
                    'fields': 'userEnteredValue,userEnteredFormat',
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': legend_row + 1,
                        'endRowIndex': legend_row + 2,
                        'startColumnIndex': 0,
                        'endColumnIndex': 2
                    }
                }
            })
            
            # Add neutral sentiment legend
            requests.append({
                'updateCells': {
                    'rows': [{
                        'values': [
                            {'userEnteredValue': {'stringValue': 'Neutral'},
                             'userEnteredFormat': {'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}}},
                            {'userEnteredValue': {'stringValue': '50-79'},
                             'userEnteredFormat': {'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}}}
                        ]
                    }],
                    'fields': 'userEnteredValue,userEnteredFormat',
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': legend_row + 2,
                        'endRowIndex': legend_row + 3,
                        'startColumnIndex': 0,
                        'endColumnIndex': 2
                    }
                }
            })
            
            # Add negative sentiment legend
            requests.append({
                'updateCells': {
                    'rows': [{
                        'values': [
                            {'userEnteredValue': {'stringValue': 'Negative'},
                             'userEnteredFormat': {'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}}},
                            {'userEnteredValue': {'stringValue': '0-49'},
                             'userEnteredFormat': {'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}}}
                        ]
                    }],
                    'fields': 'userEnteredValue,userEnteredFormat',
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': legend_row + 3,
                        'endRowIndex': legend_row + 4,
                        'startColumnIndex': 0,
                        'endColumnIndex': 2
                    }
                }
            })
            
            # Execute the formatting requests with retry logic
            for attempt in range(MAX_RETRIES):
                try:
                    body = {'requests': requests}
                    self.sheets_service.spreadsheets().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body=body
                    ).execute()
                    logger.info(f"Applied enhanced conditional formatting to {self.sheet_name}")
                    break
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Retry {attempt+1}/{MAX_RETRIES} after error: {e}")
                        time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"Error applying sentiment formatting: {e}")
    
    def _update_dashboard(self, reviews: List[Dict[str, Any]]) -> None:
        """Update dashboard metrics based on reviews data.
        
        Args:
            reviews: List of review dictionaries.
        """
        try:
            # No need to manually update most dashboard metrics as they use formulas
            # But we can potentially add more complex metrics or charts in the future
            pass
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def get_reviews(self) -> List[Dict[str, Any]]:
        """Retrieve reviews from Google Sheets.
        
        Returns:
            List of review dictionaries.
        """
        try:
            if not self.sheets_service or not self.spreadsheet_id:
                if not self.connect():
                    logger.error("Failed to connect to Google Sheets")
                    return []
            
            # Get data from sheet
            range_name = f"{self.sheet_name}!A1:Z1000"  # Adjust range as needed
            
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning("No data found in sheet")
                return []
            
            # First row contains headers
            headers = values[0]
            
            # Convert rows to dictionaries
            reviews = []
            for i in range(1, len(values)):
                row = values[i]
                # Pad row if needed
                row += [''] * (len(headers) - len(row))
                
                review = {}
                for j, header in enumerate(headers):
                    if j < len(row):
                        review[header.lower()] = row[j]
                
                reviews.append(review)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error retrieving reviews: {e}")
            return []
    
    def clear_data(self) -> bool:
        """Clear existing data in the sheet (except header row)."""
        try:
            # Get the sheet ID
            sheet_id = self._get_sheet_id(self.sheet_name)
            if not sheet_id:
                logger.error(f"Failed to get sheet ID for {self.sheet_name}")
                return False
                
            # Delete all rows except the header
            requests = [{
                'updateCells': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 1,  # Start after the header row
                        'startColumnIndex': 0
                    },
                    'fields': 'userEnteredValue'  # Clear the cell values
                }
            }]
            
            body = {'requests': requests}
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            logger.info(f"Cleared data in sheet {self.sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Google Sheets (no explicit disconnect needed)."""
        self.sheets_service = None
        logger.info("Disconnected from Google Sheets")

    def _init_services(self) -> None:
        """Initialize the Google Sheets and Drive services."""
        try:
            if not os.path.exists(self.credentials_path):
                logger.error(f"Credentials file not found at {self.credentials_path}")
                return
            
            # Load credentials - using google.oauth2 library
            try:
                creds_data = json.load(open(self.credentials_path))
                if 'type' in creds_data and creds_data['type'] == 'service_account':
                    # Service account authentication
                    from google.oauth2 import service_account
                    creds = service_account.Credentials.from_service_account_file(
                        self.credentials_path, scopes=SCOPES)
                else:
                    # OAuth client authentication
                    if not os.path.exists('token.json'):
                        from google_auth_oauthlib.flow import InstalledAppFlow
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                        # Save the credentials for the next run
                        with open('token.json', 'w') as token:
                            token.write(creds.to_json())
                    else:
                        from google.oauth2.credentials import Credentials
                        creds = Credentials.from_authorized_user_info(
                            json.load(open('token.json')), SCOPES)
                        # If credentials are expired, refresh them
                        if creds.expired and creds.refresh_token:
                            from google.auth.transport.requests import Request
                            creds.refresh(Request())
                            # Save refreshed credentials
                            with open('token.json', 'w') as token:
                                token.write(creds.to_json())
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")
                return
            
            # Build the services
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            self.drive_service = build('drive', 'v3', credentials=creds)
            
            logger.debug("Google API services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Google API services: {e}")
            self.sheets_service = None
            self.drive_service = None

    def _get_sheet_id(self, sheet_name: str) -> Optional[int]:
        """Get the sheet ID from sheet name.
        
        Args:
            sheet_name: Name of the sheet.
            
        Returns:
            Integer sheet ID if found, None otherwise.
        """
        try:
            if not self.sheets_service or not self.spreadsheet_id:
                logger.error("Sheets service or spreadsheet ID not initialized")
                return None
                
            sheet_metadata = self.sheets_service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = sheet_metadata.get('sheets', '')
            for sheet in sheets:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            return None
        except Exception as e:
            logger.error(f"Error getting sheet ID: {e}")
            return None

    def _create_dashboard_sheet(self) -> None:
        """Create a basic dashboard sheet with metrics."""
        try:
            # Add a new sheet for the dashboard
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': 'Dashboard',
                        'index': 0  # Make it the first sheet
                    }
                }
            }]
            
            body = {'requests': requests}
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Prepare basic dashboard data
            dashboard_data = [
                ["Interview Kickstart Reviews Dashboard"],
                ["Last Updated", "=NOW()"],
                [""],
                ["SUMMARY METRICS", "Value"],
                ["Total Reviews", f"=COUNTA('{self.sheet_name}'!A:A)-1"],
                ["Average Rating", f"=IFERROR(AVERAGE('{self.sheet_name}'!D:D), 0)"],
                [""],
                ["SENTIMENT DISTRIBUTION", "Count", "Percentage"],
                ["Positive", f"=COUNTIF('{self.sheet_name}'!H:H, \"POSITIVE\")", f"=IFERROR(B9/B5*100,0)&\"%\""],
                ["Neutral", f"=COUNTIF('{self.sheet_name}'!H:H, \"NEUTRAL\")", f"=IFERROR(B10/B5*100,0)&\"%\""],
                ["Negative", f"=COUNTIF('{self.sheet_name}'!H:H, \"NEGATIVE\")", f"=IFERROR(B11/B5*100,0)&\"%\""]
            ]
            
            # Update dashboard sheet with the data
            body = {'values': dashboard_data}
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Dashboard!A1",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info("Created basic dashboard sheet")
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")


# Test the Google Sheets storage if run directly
if __name__ == "__main__":
    # Sample reviews
    sample_reviews = [
        {
            "platform": "Trustpilot",
            "reviewer_name": "John Smith",
            "review_date": "2023-01-15",
            "rating": "5/5",
            "content": "Great program! Really helped me prepare for interviews.",
            "relevant": True,
            "sentiment_score": 90,
            "sentiment_category": "POSITIVE"
        },
        {
            "platform": "Course Report",
            "reviewer_name": "Jane Doe",
            "review_date": "2022-11-20",
            "rating": "3/5",
            "content": "The course was okay. Some instructors were great, others not so much.",
            "relevant": True,
            "sentiment_score": 60,
            "sentiment_category": "NEUTRAL"
        },
        {
            "platform": "Trustpilot",
            "reviewer_name": "Alice Johnson",
            "review_date": "2023-02-10",
            "rating": "1/5",
            "content": "Waste of money. The content was outdated and not helpful for interviews.",
            "relevant": True,
            "sentiment_score": 20,
            "sentiment_category": "NEGATIVE"
        }
    ]
    
    # Test Google Sheets storage
    storage = GoogleSheetsStorage()
    
    if storage.connect():
        print(f"Connected to Google Sheets. Spreadsheet ID: {storage.spreadsheet_id}")
        
        # Store sample reviews
        if storage.store_reviews(sample_reviews):
            print(f"Successfully stored {len(sample_reviews)} sample reviews")
            
            # Retrieve and print reviews
            retrieved_reviews = storage.get_reviews()
            print(f"Retrieved {len(retrieved_reviews)} reviews")
            for i, review in enumerate(retrieved_reviews):
                print(f"Review {i+1}: {review['reviewer_name']} - {review['platform']}, {review['sentiment_category']}")
        
        storage.disconnect()
    else:
        print("Failed to connect to Google Sheets. Check your credentials and configuration.") 