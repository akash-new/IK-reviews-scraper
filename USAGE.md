# IK Review Scraper Usage Guide

This document provides instructions on how to use the IK Review Scraper with Google Sheets integration.

## Basic Usage

The main script (`main.py`) integrates several components:
1. Scraping reviews from various platforms
2. Filtering reviews for relevance
3. Analyzing sentiment of reviews
4. Storing reviews in Google Sheets

### Command Line Options

```bash
# Run the full pipeline (scrape, filter, analyze sentiment, and store reviews)
python main.py

# Skip the scraping step (use existing reviews_raw.json)
python main.py --skip-scrape

# Enable storage to Google Sheets
python main.py --storage

# Skip scraping and store results in Google Sheets
python main.py --skip-scrape --storage
```

## Google Sheets Integration

Reviews are stored in Google Sheets with the following columns:
1. S.NO - Serial number
2. PLATFORM - The platform where the review was found
3. REVIEW DATE - Date of the review
4. RATING - Rating (e.g., "4/5")
5. REVIEW CONTENT - The full text of the review
6. REVIEWER NAME - Name of the reviewer
7. SENTIMENT SCORE - Numerical score for sentiment (0-100)
8. SENTIMENT CATEGORY - Category (Positive, Neutral, Negative)

### Setting Up Google Sheets Storage

1. If you haven't already, ensure you have the required Google API packages installed:
   ```bash
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
   ```

2. Set up Google Cloud credentials:
   - Follow the instructions in `credentials/README.md` to set up a Google Cloud project and create credentials
   - Place your credentials file at `credentials/google_sheets_credentials.json`

3. Share the Google Sheet with your service account email:
   - Run `python get_service_account_email.py` to find your service account email
   - Share your Google Sheet with this email address, giving Editor permissions

4. Configure storage settings:
   - Edit `config/storage_config.json` to customize your storage configuration
   - You can specify the spreadsheet ID, sheet name, and columns to include

### Enhanced Google Sheets Features

The Google Sheets integration now includes the following enhanced features:

#### 1. Enhanced Conditional Formatting
- Sentiment categories are color-coded (green for positive, yellow/grey for neutral, red for negative)
- Sentiment scores use gradient coloring (red for low scores, yellow for mid-range, green for high scores)
- A color legend is added to explain the meaning of different colors
- Better text formatting with improved alignment and font styles

#### 2. Improved Dashboard 
- A comprehensive dashboard is created automatically as the first sheet in your spreadsheet
- Dashboard includes:
  - Summary metrics (total reviews, average rating, sentiment breakdowns)
  - Pie chart showing sentiment distribution
  - Bar chart showing platform distribution
  - Histogram of sentiment scores
  - Dynamic calculation of platform-specific statistics
- Dashboard is automatically refreshed when new data is added

#### 3. Incremental Updates
- Enable incremental updates in `config/storage_config.json` by setting `"incremental_updates": true`
- When enabled, new reviews are appended to existing data rather than replacing it
- The system uses content and platform info to detect and avoid duplicate reviews
- This preserves historical data and improves performance for large datasets

#### 4. Error Handling and Recovery
- Robust error detection and handling for network issues, API limits, and authentication problems
- Detailed error logging with specific recovery suggestions
- Automatic retry logic for transient errors
- Graceful fallback to full refresh if incremental update fails

### Configuring Enhanced Features

You can configure these enhanced features in `config/storage_config.json`:

```json
{
  "google_sheets": {
    "enabled": true,
    "credentials_path": "credentials/google_sheets_credentials.json",
    "spreadsheet_id": "your-spreadsheet-id",
    "sheet_name": "IK_Reviews",
    "columns": ["s_no", "platform", "review_date", "rating", "content", 
               "reviewer_name", "sentiment_score", "sentiment_category"],
    "format_by_sentiment": true,
    "create_dashboard": true,
    "incremental_updates": true,
    "error_handling": {
      "max_retries": 3,
      "retry_delay": 5,
      "log_errors": true
    },
    "dashboard_options": {
      "show_platform_distribution": true,
      "show_sentiment_distribution": true,
      "show_score_histogram": true,
      "add_color_legend": true
    }
  }
}
```

### Troubleshooting Google Sheets Integration

If you encounter issues with Google Sheets storage:

1. Check that your credentials file is valid:
   ```bash
   python test_credentials.py
   ```

2. Create the required sheet if it doesn't exist:
   ```bash
   python create_sheet.py
   ```

3. Check the structure of your reviews:
   ```bash
   python check_review_structure.py
   ```

4. Common error messages and solutions:
   - "Quota exceeded" - Wait and try again later, or create a new project with new API keys
   - "Invalid grant" - Refresh or recreate your credentials file
   - "Socket timeout" - Check your internet connection and try again
   - "Sheet not found" - Verify your spreadsheet ID and sheet name are correct

## Configuration Files

The script uses several configuration files:

- `config/filter_config.json`: Configures which platforms to filter and filtering behavior
- `config/sentiment_config.json`: Configures sentiment analysis behavior
- `config/storage_config.json`: Configures Google Sheets storage

## Output Files

The script produces the following output files:

- `reviews_raw.json`: Raw scraped reviews (created during scraping)
- `reviews_analyzed.json`: Analyzed reviews with relevance and sentiment information
- Google Sheets document with all reviews and their analysis 

## Sentiment Analysis

The IK Review Scraper performs sentiment analysis on reviews using two methods:

1. **Google Gemini API (Preferred)**: When the `google-generativeai` package is installed and a valid API key is set in the environment variable `GEMINI_API_KEY`, the script will use the Gemini model for more accurate sentiment analysis.

2. **Built-in Fallback Analysis**: When Gemini is not available, the script uses a comprehensive built-in sentiment analyzer that examines positive and negative words and phrases to determine sentiment.

Sentiment scores range from 0-100:
- 0-49: Negative sentiment
- 50-79: Neutral sentiment
- 80-100: Positive sentiment

### Setting up Google Gemini for Enhanced Sentiment Analysis

To enable the Gemini API for improved sentiment analysis:

1. Install the required package:
   ```
   pip install google-generativeai
   ```

2. Set your Gemini API key as an environment variable:
   ```
   export GEMINI_API_KEY="your-api-key-here"
   ```

3. Run the script as usual. The script will automatically use Gemini if available.

The sentiment analysis results will be displayed in the console output and stored in the Google Sheets (if storage is enabled). 