#!/usr/bin/env python3
"""
Test script for the sentiment analysis module.

This script tests the SentimentAnalyzer class on some sample reviews
to ensure it's working correctly.
"""

import json
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ensure relative imports work correctly
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import sentiment analyzer
from sentiment.sentiment_analyzer import SentimentAnalyzer

# Sample reviews
SAMPLE_REVIEWS = [
    {
        "platform": "Trustpilot",
        "reviewer_name": "John Smith",
        "review_date": "2023-06-15",
        "rating": 5,
        "content": "I recently completed the Interview Kickstart program and it was excellent! The instructors were knowledgeable and the curriculum was comprehensive. I landed a job at a FAANG company within a month of completing the program. Highly recommended!",
        "relevant": True
    },
    {
        "platform": "Trustpilot",
        "reviewer_name": "Jane Doe",
        "review_date": "2023-07-20",
        "rating": 3,
        "content": "Interview Kickstart was okay. Some parts were useful, but I found the program overpriced for what it offers. The mock interviews were helpful, but the curriculum could use some updating.",
        "relevant": True
    },
    {
        "platform": "Course Report",
        "reviewer_name": "Alice Johnson",
        "review_date": "2023-08-10",
        "rating": 1,
        "content": "I wasted my money on Interview Kickstart. The content was outdated, the instructors were unprepared, and the support was terrible. I wouldn't recommend this program to anyone.",
        "relevant": True
    },
    {
        "platform": "Course Report",
        "reviewer_name": "Bob Wilson",
        "review_date": "2023-09-05",
        "rating": 4,
        "content": "The algorithm training at Interview Kickstart helped me improve my problem-solving skills. The system design content was excellent too. However, I think the behavioral interview preparation could be better.",
        "relevant": True
    }
]


def main():
    """Main function to test the sentiment analyzer."""
    logger.info("Testing SentimentAnalyzer...")

    # Create the analyzer
    analyzer = SentimentAnalyzer()
    
    # Analyze the sample reviews
    analyzed_reviews = analyzer.analyze_reviews(SAMPLE_REVIEWS)
    
    # Print results
    print("\nSENTIMENT ANALYSIS RESULTS:\n")
    print("=" * 80)
    
    for i, review in enumerate(analyzed_reviews, 1):
        platform = review.get("platform", "Unknown")
        reviewer = review.get("reviewer_name", "Anonymous")
        content = review.get("content", "")[:100] + "..." if len(review.get("content", "")) > 100 else review.get("content", "")
        rating = review.get("rating", "N/A")
        
        sentiment = review.get("sentiment", {})
        sentiment_score = sentiment.get("score", "N/A")
        sentiment_category = sentiment.get("category", "N/A")
        
        print(f"Review #{i} - {platform} - {reviewer} - Rating: {rating}/5")
        print(f"Content: {content}")
        print(f"Sentiment: {sentiment_category.upper()} (Score: {sentiment_score}/100)")
        print("-" * 80)
    
    # Calculate sentiment statistics
    sentiment_counts = {
        "positive": sum(1 for r in analyzed_reviews if r.get("sentiment", {}).get("category") == "positive"),
        "neutral": sum(1 for r in analyzed_reviews if r.get("sentiment", {}).get("category") == "neutral"),
        "negative": sum(1 for r in analyzed_reviews if r.get("sentiment", {}).get("category") == "negative")
    }
    
    total = len(analyzed_reviews)
    
    print("\nSUMMARY:")
    print(f"Total reviews: {total}")
    for category, count in sentiment_counts.items():
        percentage = count / total * 100 if total > 0 else 0
        print(f"{category.capitalize()}: {count} ({percentage:.1f}%)")
    
    # Save results to a file
    output_file = "test_sentiment_results.json"
    try:
        with open(output_file, "w") as f:
            json.dump(analyzed_reviews, f, indent=2)
        print(f"\nResults saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save results: {str(e)}")


if __name__ == "__main__":
    main() 