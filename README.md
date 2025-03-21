# Interview Kickstart Review Scraper v2

A tool to scrape, analyze, and export reviews for Interview Kickstart from multiple review platforms.

## Features

- **Multi-Platform Scraping**: Scrape reviews from Trustpilot and Course Report
- **Pagination Support**: Configure maximum pages to scrape for comprehensive review collection
- **Sentiment Analysis**: Analyze the sentiment of reviews using either Google Gemini API or a fallback method
- **Google Sheets Export**: Export reviews to Google Sheets with platform-specific tabs
- **Batch Processing**: Process reviews in batches to avoid API rate limits
- **Robust Error Handling**: Gracefully handle network issues and platform-specific HTML structures

## Project Structure

```
IK-Review-Scraper-v2/
├── config/                  # Configuration files and classes
│   ├── scraper_config.py    # Scraper configuration
│   ├── sentiment_config.py  # Sentiment analysis configuration
│   └── sentiment_config.json # Sentiment analysis settings
├── export/                  # Export functionality
│   └── google_sheets_exporter.py # Google Sheets export
├── scraper/                 # Scraping functionality
│   └── scraper.py           # Main scraper module 
├── sentiment/               # Sentiment analysis functionality
│   └── sentiment_analyzer.py # Sentiment analyzer with Gemini support
├── .env                     # Environment variables (API keys)
├── main.py                  # Main script to run the pipeline
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env`:
   ```
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   GEMINI_API_KEY=your_gemini_api_key  # Optional, for sentiment analysis
   GOOGLE_CREDENTIALS_PATH=path/to/credentials.json  # For Google Sheets export
   GOOGLE_SPREADSHEET_ID=your_spreadsheet_id  # For Google Sheets export
   ```

3. Configure settings:
   - Modify `config/scraper_config.py` to update platform URLs
   - Adjust `config/sentiment_config.json` to configure sentiment analysis

## Usage

Basic usage with Trustpilot:
```
python main.py --platforms Trustpilot --max-pages 3
```

Scrape multiple platforms and export to Google Sheets:
```
python main.py --platforms Trustpilot "Course Report" --max-pages 3 --export-to-sheets
```

Full options:
```
python main.py --help

Arguments:
  --platforms PLATFORMS [PLATFORMS ...]  Specific platforms to scrape (e.g., Trustpilot, 'Course Report')
  --max-pages MAX_PAGES     Maximum number of pages to scrape per platform (default: 1)
  --request-delay REQUEST_DELAY  Delay between requests in seconds (default: 2.0)
  --use-gemini              Use Google Gemini API for sentiment analysis
  --force-gemini            Force using Gemini API even if disabled in config
  --export-to-sheets        Export results to Google Sheets
  --rename-ik-reviews       Rename IK_Reviews tab to Trustpilot in Google Sheets
  --output-file OUTPUT_FILE Output file for scraped reviews (JSON)
```

## Platform-Specific Notes

### Trustpilot
- Reviews are extracted with star ratings, reviewer names, and review dates
- Pagination works by appending `?page=N` to the base URL

### Course Report
- Reviews include overall experience, instructor, curriculum, and job assistance ratings
- Pagination is more complex as the URL doesn't change when navigating pages
  
## Output Formats

### JSON Files
- `trustpilot_reviews.json` - Raw Trustpilot reviews
- `course_report_reviews.json` - Raw Course Report reviews
- `trustpilot_reviews_with_sentiment.json` - Trustpilot reviews with sentiment analysis
- `course_report_reviews_with_sentiment.json` - Course Report reviews with sentiment analysis
- `all_reviews.json` - Combined reviews from all platforms

### Google Sheets
- `Trustpilot` tab - All Trustpilot reviews with sentiment analysis
- `Course Report` tab - All Course Report reviews with sentiment analysis