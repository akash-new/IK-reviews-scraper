import logging
from typing import Dict, List, Any, Optional, Tuple
import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_review_for_storage(review: Dict[str, Any], columns: List[str], index: int = None) -> List[Any]:
    """Format a review dictionary into a list of values based on the columns order.
    
    Args:
        review: The review dictionary.
        columns: List of column names in the desired order.
        index: Optional index to use for s_no field (defaults to None).
        
    Returns:
        List of values ordered according to the columns list.
    """
    result = []
    for column in columns:
        if column == "s_no":
            # For serial number, use the provided index or 0 if not provided
            result.append(index + 1 if index is not None else "")
        elif column == "platform":
            result.append(review.get("platform", ""))
        elif column == "reviewer_name":
            result.append(review.get("reviewer_name", ""))
        elif column == "review_date":
            # Format the date if needed
            date_str = review.get("review_date", "")
            try:
                # Attempt to parse and format the date
                if date_str:
                    # Handle various date formats
                    date_formats = [
                        "%Y-%m-%d",
                        "%m/%d/%Y", 
                        "%d/%m/%Y",
                        "%B %d, %Y"
                    ]
                    
                    date_obj = None
                    for fmt in date_formats:
                        try:
                            date_obj = datetime.datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if date_obj:
                        # Use a standardized format for storage
                        date_str = date_obj.strftime("%Y-%m-%d")
                result.append(date_str)
            except Exception as e:
                logger.warning(f"Error formatting date '{date_str}': {e}")
                result.append(date_str)
        elif column == "rating":
            # Convert rating to numerical value if possible
            rating = review.get("rating", "")
            try:
                # Extract numerical part if it's in format like "4/5"
                if isinstance(rating, str) and "/" in rating:
                    match = re.search(r'(\d+)/(\d+)', rating)
                    if match:
                        num, denom = match.groups()
                        # Keep the format "4/5" as requested
                        result.append(rating)
                    else:
                        result.append(rating)
                elif isinstance(rating, (int, float)):
                    # Format numeric ratings as X/5
                    normalized = (float(rating) / 5) * 5  # Ensure it's on a 5-point scale
                    result.append(f"{normalized:.1f}/5")
                else:
                    result.append(rating)
            except Exception as e:
                logger.warning(f"Error formatting rating '{rating}': {e}")
                result.append(rating)
        elif column == "content":
            # Get content, falling back to review_content
            # In this dataset, review_content is the primary field
            content = review.get("review_content", review.get("content", ""))
            # Truncate very long content to avoid Google Sheets API errors (max 50,000 chars per cell)
            if len(content) > 40000:  # Use 40,000 as a safe limit
                content = content[:40000] + "... (content truncated due to length)"
                logger.warning(f"Content truncated for review due to excessive length ({len(content)} characters)")
            result.append(content)
        elif column == "relevant":
            # Format as "Yes" or "No" for better readability
            is_relevant = review.get("relevant", False)
            if isinstance(is_relevant, bool):
                result.append("Yes" if is_relevant else "No")
            else:
                # If it's already a string, convert to proper case
                if str(is_relevant).lower() in ['true', 'yes', '1']:
                    result.append("Yes")
                else:
                    result.append("No")
        elif column == "sentiment_score":
            # Format as integer if possible
            # First check if sentiment is a nested object
            if isinstance(review.get("sentiment"), dict) and "score" in review["sentiment"]:
                score = review["sentiment"]["score"]
            else:
                score = review.get("sentiment_score", "")
            
            try:
                if score:
                    score = int(score)
                result.append(score)
            except Exception as e:
                logger.warning(f"Error formatting sentiment score '{score}': {e}")
                result.append(score)
        elif column == "sentiment_category":
            # Format properly with first letter capitalized
            # First check if sentiment is a nested object
            if isinstance(review.get("sentiment"), dict) and "category" in review["sentiment"]:
                category = review["sentiment"]["category"].upper()
            else:
                category = review.get("sentiment_category", "").upper()
            
            if category:
                result.append(category.title())
            else:
                result.append("")
        else:
            # For any other columns, just get the value or empty string
            result.append(review.get(column, ""))
    
    return result


def get_cell_format_for_sentiment(sentiment_category: str) -> Tuple[str, str, str]:
    """Get cell formatting values for a sentiment category.
    
    Args:
        sentiment_category: The sentiment category (POSITIVE, NEUTRAL, NEGATIVE).
        
    Returns:
        Tuple of (background_color, text_color, font_weight)
    """
    sentiment_upper = sentiment_category.upper()
    
    if sentiment_upper == "POSITIVE":
        return ("#e6f4ea", "#00701a", "bold")  # Light green background, dark green text
    elif sentiment_upper == "NEGATIVE":
        return ("#fce8e6", "#c5221f", "bold")  # Light red background, dark red text
    elif sentiment_upper == "NEUTRAL":
        return ("#f1f3f4", "#202124", "normal")  # Light gray background, dark gray text
    else:
        return ("#ffffff", "#000000", "normal")  # Default white background, black text


def create_dashboard_data(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create dashboard data from reviews.
    
    Args:
        reviews: List of review dictionaries.
        
    Returns:
        Dictionary with dashboard data metrics.
    """
    total_reviews = len(reviews)
    if total_reviews == 0:
        return {
            "total_reviews": 0,
            "relevant_reviews": 0,
            "sentiment_counts": {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0},
            "platform_counts": {},
            "average_rating": 0.0,
            "relevant_percentage": 0.0,
            "sentiment_percentages": {"POSITIVE": 0.0, "NEUTRAL": 0.0, "NEGATIVE": 0.0}
        }
    
    # Count relevant reviews
    relevant_reviews = sum(1 for r in reviews if r.get("relevant", False))
    
    # Count by sentiment
    sentiment_counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
    for review in reviews:
        sentiment = review.get("sentiment_category", "").upper()
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
        else:
            sentiment_counts["NEUTRAL"] += 1  # Default to neutral if category is invalid
    
    # Count by platform
    platform_counts = {}
    for review in reviews:
        platform = review.get("platform", "Unknown")
        if platform in platform_counts:
            platform_counts[platform] += 1
        else:
            platform_counts[platform] = 1
    
    # Calculate average rating
    total_rating = 0.0
    rating_count = 0
    for review in reviews:
        rating = review.get("rating", None)
        try:
            # Handle "4/5" format
            if isinstance(rating, str) and "/" in rating:
                match = re.search(r'(\d+)/(\d+)', rating)
                if match:
                    num, denom = match.groups()
                    numerical_rating = float(num) / float(denom) * 5
                    total_rating += numerical_rating
                    rating_count += 1
            elif isinstance(rating, (int, float)):
                total_rating += float(rating)
                rating_count += 1
        except (ValueError, TypeError):
            pass
    
    average_rating = total_rating / rating_count if rating_count > 0 else 0.0
    
    # Calculate percentages
    relevant_percentage = (relevant_reviews / total_reviews) * 100 if total_reviews > 0 else 0.0
    
    sentiment_percentages = {}
    for sentiment, count in sentiment_counts.items():
        sentiment_percentages[sentiment] = (count / total_reviews) * 100 if total_reviews > 0 else 0.0
    
    return {
        "total_reviews": total_reviews,
        "relevant_reviews": relevant_reviews,
        "sentiment_counts": sentiment_counts,
        "platform_counts": platform_counts,
        "average_rating": average_rating,
        "relevant_percentage": relevant_percentage,
        "sentiment_percentages": sentiment_percentages
    } 