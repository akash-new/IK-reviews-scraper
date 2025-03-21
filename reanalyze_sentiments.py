#!/usr/bin/env python3
"""
Script to reanalyze sentiments of reviews in reviews_raw.json.
"""

import json
import logging
import os
from typing import Dict, Any, List

from sentiment.sentiment_analyzer import SentimentAnalyzer

# Set up logging - set to DEBUG level
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_reviews(file_path: str) -> List[Dict[str, Any]]:
    """
    Load reviews from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file.
        
    Returns:
        List[Dict[str, Any]]: List of review dictionaries.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return []

def save_reviews(reviews: List[Dict[str, Any]], file_path: str) -> bool:
    """
    Save reviews to a JSON file.
    
    Args:
        reviews (List[Dict[str, Any]]): List of review dictionaries.
        file_path (str): Path to save the JSON file.
        
    Returns:
        bool: True if save was successful, False otherwise.
    """
    try:
        # Make sure we have a valid file path
        if not file_path:
            file_path = "./reviews_reanalyzed.json"
            
        logger.debug(f"Saving to file path: {file_path}")
        # Don't try to create directories since it's just a file in the current dir
        with open(file_path, 'w') as f:
            json.dump(reviews, f, indent=2)
        logger.info(f"Saved {len(reviews)} reviews to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save reviews to {file_path}: {str(e)}")
        return False

def reanalyze_sentiments(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Reanalyze the sentiments of reviews.
    
    Args:
        reviews (List[Dict[str, Any]]): List of review dictionaries.
        
    Returns:
        List[Dict[str, Any]]: Reviews with updated sentiment data.
    """
    # Initialize sentiment analyzer
    analyzer = SentimentAnalyzer()
    
    # Force disable Gemini for debugging - use our improved fallback
    analyzer.gemini = False
    logger.debug("Using fallback sentiment analysis method for all reviews")
    
    total = len(reviews)
    analyzed = 0
    
    logger.info(f"Reanalyzing sentiments for {total} reviews")
    
    for review in reviews:
        # Get the review content - prioritize the review_content field
        content = review.get("review_content", review.get("content", ""))
        
        if content:
            # Log review preview for debugging
            content_preview = content[:100] + "..." if len(content) > 100 else content
            logger.debug(f"Analyzing review {analyzed+1}: {content_preview}")
            
            # Clear cache for this review if it exists
            cache_path = analyzer._get_cache_path(content)
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                    logger.debug(f"Cleared cache for review {analyzed+1}")
                except:
                    pass
            
            # Analyze sentiment
            sentiment = analyzer.analyze_text(content)
            
            # Log sentiment result
            logger.info(f"Review {analyzed+1} sentiment: {sentiment}")
            
            # Add sentiment to the review
            review["sentiment"] = sentiment
            
            # Increment counter
            analyzed += 1
            
            if analyzed % 5 == 0 or analyzed == total:
                logger.info(f"Analyzed sentiment for {analyzed}/{total} reviews")
    
    logger.info(f"Completed sentiment analysis for {analyzed} reviews")
    return reviews

def print_sentiment_stats(reviews: List[Dict[str, Any]]) -> None:
    """
    Print sentiment statistics for a list of reviews.
    
    Args:
        reviews (List[Dict[str, Any]]): List of review dictionaries.
    """
    if not reviews:
        logger.info("No reviews to analyze.")
        return
    
    # Count sentiment categories
    positive_count = 0
    neutral_count = 0
    negative_count = 0
    unknown_count = 0
    
    # Collect scores
    scores = []
    
    for review in reviews:
        sentiment = review.get("sentiment", {})
        category = sentiment.get("category", "unknown")
        score = sentiment.get("score")
        
        if score is not None:
            scores.append(score)
        
        if category == "positive":
            positive_count += 1
        elif category == "neutral":
            neutral_count += 1
        elif category == "negative":
            negative_count += 1
        else:
            unknown_count += 1
    
    total = len(reviews)
    
    # Print statistics
    logger.info("\nSENTIMENT ANALYSIS RESULTS:")
    logger.info(f"Total reviews: {total}")
    logger.info(f"Positive: {positive_count} ({positive_count/total*100:.1f}%)")
    logger.info(f"Neutral: {neutral_count} ({neutral_count/total*100:.1f}%)")
    logger.info(f"Negative: {negative_count} ({negative_count/total*100:.1f}%)")
    
    if scores:
        logger.info(f"Score range: {min(scores)} - {max(scores)}")
        logger.info(f"Average score: {sum(scores)/len(scores):.1f}")

def main():
    """
    Main function to reanalyze sentiments of reviews.
    """
    # Load raw reviews
    raw_reviews = load_reviews("reviews_raw.json")
    
    if not raw_reviews:
        logger.error("No reviews to analyze. Exiting.")
        return
    
    # Reanalyze sentiments
    analyzed_reviews = reanalyze_sentiments(raw_reviews)
    
    # Print sentiment statistics
    print_sentiment_stats(analyzed_reviews)
    
    # Save analyzed reviews
    save_reviews(analyzed_reviews, "reviews_reanalyzed.json")
    
    logger.info("Sentiment reanalysis complete.")

if __name__ == "__main__":
    main() 