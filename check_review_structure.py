#!/usr/bin/env python3
"""
Utility script to check the structure of reviews in reviews_raw.json
"""

import json
import os
import sys

def main():
    """Main function to examine review structure."""
    # Load reviews from file
    reviews_file = "reviews_raw.json"
    
    if not os.path.exists(reviews_file):
        print(f"Error: File '{reviews_file}' not found")
        return
    
    try:
        with open(reviews_file, "r") as f:
            reviews = json.load(f)
    except Exception as e:
        print(f"Error loading reviews: {e}")
        return
    
    if not reviews:
        print("No reviews found in file")
        return
    
    print(f"Loaded {len(reviews)} reviews from {reviews_file}")
    
    # Print structure of first review
    first_review = reviews[0]
    print("\nStructure of first review:")
    for key, value in first_review.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"{key}: (string of length {len(value)})")
        else:
            print(f"{key}: {value}")
    
    # Check for sentiment and content fields
    sentiment_fields = ["sentiment", "sentiment_score", "sentiment_category"]
    content_fields = ["content", "review_content"]
    
    # Check if all reviews have these fields
    sentiment_count = sum(1 for r in reviews if any(field in r for field in sentiment_fields))
    content_count = sum(1 for r in reviews if any(field in r for field in content_fields))
    
    print(f"\nReviews with sentiment fields: {sentiment_count}/{len(reviews)}")
    print(f"Reviews with content fields: {content_count}/{len(reviews)}")
    
    # Load reviews_analyzed.json to check post-processing structure
    analyzed_file = "reviews_analyzed.json"
    if os.path.exists(analyzed_file):
        try:
            with open(analyzed_file, "r") as f:
                analyzed_reviews = json.load(f)
                
            if analyzed_reviews:
                print(f"\nLoaded {len(analyzed_reviews)} reviews from {analyzed_file}")
                
                # Print structure of first analyzed review
                first_analyzed = analyzed_reviews[0]
                print("\nStructure of first analyzed review:")
                for key, value in first_analyzed.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"{key}: (string of length {len(value)})")
                    elif isinstance(value, dict):
                        print(f"{key}: (dictionary with keys {list(value.keys())})")
                    else:
                        print(f"{key}: {value}")
                
                # Check for needed fields
                sentiment_score_count = sum(1 for r in analyzed_reviews if "sentiment_score" in r)
                sentiment_category_count = sum(1 for r in analyzed_reviews if "sentiment_category" in r)
                nested_sentiment_count = sum(1 for r in analyzed_reviews if isinstance(r.get("sentiment"), dict))
                
                print(f"\nAnalyzed reviews with sentiment_score field: {sentiment_score_count}/{len(analyzed_reviews)}")
                print(f"Analyzed reviews with sentiment_category field: {sentiment_category_count}/{len(analyzed_reviews)}")
                print(f"Analyzed reviews with nested sentiment object: {nested_sentiment_count}/{len(analyzed_reviews)}")
                
        except Exception as e:
            print(f"Error loading analyzed reviews: {e}")
    
if __name__ == "__main__":
    main() 