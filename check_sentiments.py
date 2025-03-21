#!/usr/bin/env python3
"""
Script to check the sentiment scores of reviews in the analyzed data.
"""

import json
import random
import os
from typing import Dict, Any, List

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
        print(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {file_path}")
        return []

def print_review_summary(review: Dict[str, Any], index: int) -> None:
    """
    Print a summary of a review.
    
    Args:
        review (Dict[str, Any]): Review dictionary.
        index (int): Index of the review.
    """
    # Get content from either review_content or content field
    content = review.get("review_content", review.get("content", ""))
    
    # Truncate content for display
    content_preview = content[:150] + "..." if len(content) > 150 else content
    
    # Get sentiment data
    sentiment = review.get("sentiment", {})
    score = sentiment.get("score", "N/A")
    category = sentiment.get("category", "N/A")
    
    # Get platform
    platform = review.get("platform", "Unknown")
    
    # Print review summary
    print(f"Review {index+1} - Platform: {platform}")
    print(f"Content:\n{content_preview}")
    print(f"Sentiment: {category.upper()} (Score: {score})")
    print("-" * 80)

def main():
    """
    Main function to check the sentiment scores of reviews.
    """
    # Load analyzed reviews
    reviews = load_reviews("reviews_analyzed.json")
    
    if not reviews:
        print("No reviews found.")
        return
    
    print(f"Total reviews: {len(reviews)}")
    
    # Get sentiment statistics
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0, "unknown": 0}
    sentiment_scores = []
    
    for review in reviews:
        sentiment = review.get("sentiment", {})
        category = sentiment.get("category", "unknown")
        score = sentiment.get("score")
        
        if score is not None:
            sentiment_scores.append(score)
        
        if category in sentiment_counts:
            sentiment_counts[category] += 1
        else:
            sentiment_counts["unknown"] += 1
    
    # Print sentiment statistics
    print("\nSentiment Statistics:")
    print(f"Positive: {sentiment_counts['positive']} ({sentiment_counts['positive']/len(reviews)*100:.1f}%)")
    print(f"Neutral: {sentiment_counts['neutral']} ({sentiment_counts['neutral']/len(reviews)*100:.1f}%)")
    print(f"Negative: {sentiment_counts['negative']} ({sentiment_counts['negative']/len(reviews)*100:.1f}%)")
    
    if sentiment_scores:
        print(f"\nSentiment Score Range: {min(sentiment_scores)} - {max(sentiment_scores)}")
        print(f"Average Sentiment Score: {sum(sentiment_scores)/len(sentiment_scores):.1f}")
    
    # Print sample reviews
    print("\nSample Reviews:")
    samples = random.sample(reviews, min(5, len(reviews)))
    for i, review in enumerate(samples):
        print_review_summary(review, i)
    
    # Check if all scores are the same
    if sentiment_scores and min(sentiment_scores) == max(sentiment_scores):
        print("\nWARNING: All sentiment scores are the same value!")
        print("This suggests the sentiment analysis may not be working correctly.")

if __name__ == "__main__":
    main() 