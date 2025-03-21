#!/usr/bin/env python3
"""
Interview Kickstart Review Scraper

This script integrates all components of the IK Review Scraper:
1. Configuration
2. Scraping
3. Sentiment Analysis
4. Data Export to Google Sheets

Run this script to scrape reviews, analyze sentiment, and export results to Google Sheets.

Usage:
    python main.py --platforms Trustpilot "Course Report" --max-pages 3 --export-to-sheets
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import project modules
try:
    from config.scraper_config import ScraperConfig
    from config.sentiment_config import SentimentConfig
    from scraper.scraper import Scraper
    from sentiment.sentiment_analyzer import SentimentAnalyzer
    
    # Handle Google Sheets exporter import separately to handle missing dependencies
    try:
        from export.google_sheets_exporter import GoogleSheetsExporter
        GOOGLE_SHEETS_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"Google Sheets export module not available: {str(e)}")
        GOOGLE_SHEETS_AVAILABLE = False
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    logger.info("Ensure you're running from the project root directory")
    sys.exit(1)


def main():
    """Main function to run the review scraping pipeline."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scrape and analyze reviews from various platforms")
    parser.add_argument("--platforms", type=str, nargs="+", default=["Course Report"],
                      help="Platforms to scrape (default: Course Report)")
    parser.add_argument("--max-pages", type=int, default=1,
                      help="Maximum number of pages to scrape per platform")
    parser.add_argument("--request-delay", type=float, default=2.0,
                      help="Delay between requests in seconds")
    parser.add_argument("--use-gemini", action="store_true", help="Use Google Gemini API for sentiment analysis")
    parser.add_argument("--force-gemini", action="store_true", help="Force using Gemini API even if disabled in config")
    parser.add_argument("--export-to-sheets", action="store_true", help="Export results to Google Sheets")
    parser.add_argument("--rename-ik-reviews", action="store_true", help="Rename IK_Reviews tab to Trustpilot in Google Sheets")
    parser.add_argument("--output-file", default="all_reviews.json", help="Output file for scraped reviews (JSON)")
    args = parser.parse_args()
    
    # Initialize configuration
    scraper_config = ScraperConfig()
    sentiment_config = SentimentConfig.load()
    
    # Override sentiment config if requested
    if args.use_gemini:
        sentiment_config.use_gemini = True
    if args.force_gemini:
        sentiment_config.force_gemini = True
    
    # Save any config changes
    sentiment_config.save_config()
    
    # Initialize scraper
    scraper = Scraper(config=scraper_config, max_pages=args.max_pages, request_delay=args.request_delay)
    
    # Determine which platforms to scrape
    platforms_to_scrape = []
    if args.platforms:
        # Scrape only specified platforms
        for platform_name in args.platforms:
            platform = scraper_config.get_platform(platform_name)
            if platform and platform.scrape_allowed:
                platforms_to_scrape.append(platform)
            else:
                logger.warning(f"Platform '{platform_name}' not found or scraping not allowed")
    else:
        # Default: scrape all allowed platforms
        platforms_to_scrape = scraper_config.get_scrapeable_platforms()
    
    # Check if we have platforms to scrape
    if not platforms_to_scrape:
        logger.error("No valid platforms to scrape. Use --platforms to specify platforms.")
        return
    
    logger.info(f"Starting scraper for platforms: {', '.join([p.name for p in platforms_to_scrape])}")
    
    # Dictionary to hold reviews by platform
    reviews_by_platform = {}
    all_reviews = []
    
    # Scrape each platform
    for platform in platforms_to_scrape:
        try:
            logger.info(f"Scraping {platform.name}...")
            platform_reviews = scraper.scrape_platform(platform)
            
            # Store reviews by platform and add to all reviews
            if platform_reviews:
                reviews_by_platform[platform.name] = platform_reviews
                all_reviews.extend(platform_reviews)
                
                # Save platform-specific reviews to file
                platform_file = f"{platform.name.lower().replace(' ', '_')}_reviews.json"
                with open(platform_file, 'w') as f:
                    json.dump(platform_reviews, f, indent=2)
                logger.info(f"Saved {len(platform_reviews)} {platform.name} reviews to {platform_file}")
        
        except Exception as e:
            logger.error(f"Error scraping {platform.name}: {str(e)}")
    
    # Save all reviews to file
    with open(args.output_file, 'w') as f:
        json.dump(all_reviews, f, indent=2)
    logger.info(f"Saved all {len(all_reviews)} reviews to {args.output_file}")
    
    # Skip sentiment analysis if no reviews were collected
    if not all_reviews:
        logger.warning("No reviews collected, skipping sentiment analysis and export")
        return
    
    # Analyze sentiment
    logger.info("Analyzing sentiment of reviews...")
    sentiment_analyzer = SentimentAnalyzer(sentiment_config)
    
    # Process reviews by platform
    for platform_name, platform_reviews in reviews_by_platform.items():
        try:
            # Analyze reviews in batches with the enhanced sentiment analyzer
            logger.info(f"Analyzing sentiment for {len(platform_reviews)} {platform_name} reviews")
            sentiment_results = sentiment_analyzer.analyze_reviews(platform_reviews)
            
            # Update reviews with sentiment results
            for i, review in enumerate(platform_reviews):
                if i < len(sentiment_results):
                    review["sentiment_score"] = sentiment_results[i]["score"]
                    review["sentiment_category"] = sentiment_results[i]["category"]
            
            # Save updated reviews with sentiment
            platform_file = f"{platform_name.lower().replace(' ', '_')}_reviews_with_sentiment.json"
            with open(platform_file, 'w') as f:
                json.dump(platform_reviews, f, indent=2)
            logger.info(f"Saved {platform_name} reviews with sentiment to {platform_file}")
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {platform_name}: {str(e)}")
    
    # Export to Google Sheets if requested
    if args.export_to_sheets and GOOGLE_SHEETS_AVAILABLE:
        try:
            logger.info("Exporting reviews to Google Sheets...")
            
            # Initialize Google Sheets exporter
            exporter = GoogleSheetsExporter()
            
            # Get reviews by platform
            trustpilot_reviews = reviews_by_platform.get("Trustpilot", [])
            course_report_reviews = reviews_by_platform.get("Course Report", [])
            
            # Rename IK_Reviews tab to Trustpilot if requested
            if args.rename_ik_reviews:
                try:
                    # Check if IK_Reviews tab exists
                    try:
                        ik_reviews_tab = exporter.spreadsheet.worksheet("IK_Reviews")
                        # Rename tab if it exists
                        exporter.spreadsheet.del_worksheet(ik_reviews_tab)
                        logger.info("Deleted IK_Reviews tab")
                    except Exception as e:
                        logger.warning(f"Could not find or delete IK_Reviews tab: {str(e)}")
                        
                except Exception as e:
                    logger.error(f"Error renaming IK_Reviews tab: {str(e)}")
            
            # Export to Google Sheets
            success = exporter.export_reviews(
                trustpilot_reviews=trustpilot_reviews,
                course_report_reviews=course_report_reviews
            )
            
            if success:
                logger.info("Successfully exported reviews to Google Sheets")
            else:
                logger.error("Failed to export some or all reviews to Google Sheets")
        
        except Exception as e:
            logger.error(f"Error exporting to Google Sheets: {str(e)}")
    
    elif args.export_to_sheets and not GOOGLE_SHEETS_AVAILABLE:
        logger.error("Google Sheets export requested but dependencies not available")
        logger.error("Install required packages with: pip install gspread oauth2client")
    
    logger.info("Review scraping and analysis pipeline completed")


if __name__ == "__main__":
    main()
