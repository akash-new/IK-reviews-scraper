"""
Test script to evaluate the RelevanceFilter with real data.

This script loads the reviews from trustpilot_reviews.json and tests the
RelevanceFilter to see how it performs on real-world data.
"""

import json
import logging
from relevance_filter import RelevanceFilter

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    """Test the RelevanceFilter with real data."""
    # Load data from trustpilot_reviews.json
    try:
        with open('../trustpilot_reviews.json', 'r') as f:
            reviews = json.load(f)
        logger.info(f"Loaded {len(reviews)} reviews from trustpilot_reviews.json")
    except Exception as e:
        logger.error(f"Error loading reviews: {str(e)}")
        return
    
    # Initialize the RelevanceFilter
    filter = RelevanceFilter()
    
    # Filter the reviews
    filtered_reviews = filter.filter_reviews(reviews)
    
    # Calculate and display statistics
    relevant_count = sum(1 for r in filtered_reviews if r.get('relevant', False))
    irrelevant_count = len(filtered_reviews) - relevant_count
    
    print(f"\nTotal reviews: {len(filtered_reviews)}")
    print(f"Relevant reviews: {relevant_count} ({relevant_count/len(filtered_reviews)*100:.1f}%)")
    print(f"Irrelevant reviews: {irrelevant_count} ({irrelevant_count/len(filtered_reviews)*100:.1f}%)")
    
    # Display some examples of relevant and irrelevant reviews
    print("\n--- EXAMPLES OF RELEVANT REVIEWS ---")
    relevant_examples = [r for r in filtered_reviews if r.get('relevant', False)][:3]
    for i, review in enumerate(relevant_examples):
        print(f"\nRelevant Example #{i+1}:")
        print(f"Rating: {review.get('rating', 'N/A')}")
        print(f"Content: {review.get('review_content', '')[:150]}...")
        print("-" * 50)
    
    print("\n--- EXAMPLES OF IRRELEVANT REVIEWS ---")
    irrelevant_examples = [r for r in filtered_reviews if not r.get('relevant', False)][:3]
    for i, review in enumerate(irrelevant_examples):
        print(f"\nIrrelevant Example #{i+1}:")
        print(f"Rating: {review.get('rating', 'N/A')}")
        print(f"Content: {review.get('review_content', '')[:150]}...")
        print("-" * 50)

if __name__ == "__main__":
    main() 