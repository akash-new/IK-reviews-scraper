"""
Relevance Filtering Module for IK Review Scraper.

This module provides functionality to filter reviews based on their relevance
to Interview Kickstart using keyword matching and Gemini API.
"""

import logging
import os
import re
from typing import List, Dict, Any, Optional, Set
from dotenv import load_dotenv
import json
import time

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("google-generativeai package not installed. AI-based filtering will be disabled.")

# Basic logging setup (consistent with scraper.py)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RelevanceFilter:
    """
    Filter to determine if a review is relevant to Interview Kickstart.
    
    Uses keyword matching and optionally Gemini API for ambiguous cases.
    """

    def __init__(self, api_key: Optional[str] = None, platforms_to_filter: Optional[List[str]] = None):
        """
        Initialize the RelevanceFilter with an optional Gemini API key and platform configuration.
        
        Args:
            api_key (str, optional): Gemini API key. Defaults to the GEMINI_API_KEY environment variable.
            platforms_to_filter (List[str], optional): List of platform names to apply filtering to.
                If None, filtering will be applied to all platforms.
                Example: ['Trustpilot', 'Course Report']
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.gemini_enabled = False
        
        # Set of platforms to filter (convert to set for O(1) lookups)
        self.platforms_to_filter = set(platforms_to_filter) if platforms_to_filter else None
        
        # Configure Gemini AI if the API key is available
        if genai and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.gemini_enabled = True
                logger.info("Gemini API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {str(e)}")
        elif not genai:
            logger.warning("Gemini API not available: package not installed")
        elif not self.api_key:
            logger.warning("Gemini API not available: API key not found")
    
    def _is_company_information(self, content: str) -> bool:
        """
        Check if the content is company information rather than a review.
        
        Args:
            content (str): The content to check.
            
        Returns:
            bool: True if it's likely company information, False otherwise.
        """
        # Check for indicators of company information sections
        indicators = [
            "company details",
            "written by the company",
            "based on a student",
            "interview kickstart is a part-time",
            "interview kickstart gives students",
            "the highlight of interview kickstart",
            "after course completion",
            "since 2014",
            "contact info",
            "has trained over",
            "alums receive",
            "people also looked at"
        ]
        
        content_lower = content.lower()
        
        # Check if any of the indicators are in the content
        for indicator in indicators:
            if indicator in content_lower:
                return True
        
        # Check for structured sections that suggest company info
        sections = [
            "## company details",
            "#### written by the company",
            "#### contact info",
            "## people also looked at"
        ]
        
        for section in sections:
            if section in content_lower:
                return True
                
        # Check for very long content (usually full page scrapes with company info)
        if len(content.split()) > 200:  # Very long reviews are often full page scrapes
            # Additional checks for long content to determine if it's company info
            paragraph_count = content.count("\n\n")
            section_count = len(re.findall(r"^#{1,6} ", content, re.MULTILINE))
            
            # If there are many paragraphs and sections, it's likely a full page
            if paragraph_count > 10 and section_count > 3:
                return True
                
        return False
    
    def _is_relevant_by_keywords(self, content: str) -> bool:
        """
        Check if the content is relevant based on keyword matching.
        
        Checks for Interview Kickstart or IK mentions combined with relevant themes.
        
        Args:
            content (str): The review content to check.
            
        Returns:
            bool: True if relevant based on keywords, False otherwise.
        """
        # First check if this is company information rather than a review
        if self._is_company_information(content):
            return False
            
        # Convert to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Check for the presence of company identifiers
        company_identifiers = [
            "interview kickstart", 
            "interviewkickstart", 
            " ik ", 
            "\nik\n", 
            "ik course", 
            "ik program", 
            "ik class", 
            "ik experience"
        ]
        has_company_ref = any(identifier in content_lower for identifier in company_identifiers)
        
        # If there's no company reference, check for some special cases
        if not has_company_ref:
            if content_lower.startswith("ik ") or content_lower.endswith(" ik"):
                has_company_ref = True
            # Check for specific IK references that might not be caught by the first check
            elif re.search(r'\bik\b', content_lower):
                has_company_ref = True
        
        if not has_company_ref:
            return False
        
        # Check for relevant themes - expanded to match more patterns in reviews
        themes = [
            # Course and curriculum related
            "course", "class", "curriculum", "program", "session", "lecture", "video", "material",
            "assignment", "topic", "content", "lesson", "learning", "study", "mock interview",
            
            # Instructor related
            "instructor", "teacher", "coach", "mentor", "staff", "trainer", "educator", "professor",
            
            # Fee related
            "fee", "price", "cost", "expensive", "affordable", "worth", "value", "money", "paid", "investment",
            
            # Experience related
            "experience", "quality", "helpful", "useful", "effective", "excellent", "great", "good", "bad",
            "amazing", "impressed", "recommend", "review", "rating", "star", "feedback",
            
            # Career related
            "job", "placement", "career", "offer", "salary", "interview", "hired", "position", "opportunity",
            "skill", "preparation", "resume", "cv", "portfolio", "application", "employer", "company",
            
            # Support related
            "support", "help", "guidance", "assistance", "service", "response", "communication", "team",
            
            # Technical content
            "technical", "coding", "algorithm", "data structure", "system design", "programming", "software"
        ]
        
        # For very short content, consider it relevant if it has a company reference
        if len(content.split()) < 10:
            return True
        
        has_theme = any(theme in content_lower for theme in themes)
        
        return has_theme
    
    def _is_relevant_by_gemini(self, content: str) -> bool:
        """
        Use Gemini API to determine if the content is relevant.
        
        Args:
            content (str): The review content to check.
            
        Returns:
            bool: True if Gemini determines it's relevant, False otherwise.
        """
        if not self.gemini_enabled:
            return False
        
        try:
            prompt = (
                f"Does this text discuss Interview Kickstart's courses, instructors, fees, or overall experience? "
                f"Answer yes or no.\n\nText: \"{content}\""
            )
            
            generation_config = GenerationConfig(temperature=0.1)
            model = genai.GenerativeModel('models/gemini-1.5-pro')
            response = model.generate_content(prompt)
            
            # Extract yes/no answer
            response_text = response.text.lower().strip()
            return "yes" in response_text and "no" not in response_text[:4]
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return False
    
    def _should_filter_platform(self, platform: str) -> bool:
        """
        Determine if a platform should be filtered.
        
        Args:
            platform (str): The platform name.
            
        Returns:
            bool: True if the platform should be filtered, False otherwise.
        """
        # If platforms_to_filter is None, filter all platforms
        if self.platforms_to_filter is None:
            return True
        
        # Otherwise, only filter platforms in the set
        return platform in self.platforms_to_filter
    
    def filter_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter a list of reviews for relevance to Interview Kickstart.
        
        Args:
            reviews (List[Dict[str, Any]]): List of review dictionaries with at least a 'content' key.
            
        Returns:
            List[Dict[str, Any]]: Same list with an added 'relevant' key (True/False).
        """
        filtered_reviews = []
        filtered_count = 0  # Number of reviews actually filtered
        total_relevant = 0
        
        for review in reviews:
            try:
                # Get platform
                platform = review.get('platform', 'Unknown')
                
                # Check if we should filter this platform
                if self._should_filter_platform(platform):
                    # Get review content (handle both 'content' and 'review_content' keys)
                    content = review.get('content', review.get('review_content', ''))
                    
                    if not content:
                        logger.warning(f"Review missing content: {review}")
                        review['relevant'] = False
                    else:
                        # First check using keywords
                        relevant = self._is_relevant_by_keywords(content)
                        
                        # If not obviously relevant by keywords, try Gemini for ambiguous cases
                        if not relevant and self.gemini_enabled:
                            # For optimization, only use Gemini if there's some mention of "IK" or similar
                            # but not enough context for keyword matching
                            if re.search(r'\bik\b|\binterview kickstart\b', content.lower()):
                                relevant = self._is_relevant_by_gemini(content)
                        
                        # Add relevance flag to the review
                        review['relevant'] = relevant
                        if relevant:
                            total_relevant += 1
                    
                    filtered_count += 1
                else:
                    # For platforms we're not filtering, mark all as relevant
                    review['relevant'] = True
                    total_relevant += 1
                    
                filtered_reviews.append(review)
                
            except Exception as e:
                logger.error(f"Error processing review: {str(e)}")
                review['relevant'] = False
                filtered_reviews.append(review)
        
        # Log statistics
        if filtered_count > 0:
            relevant_filtered = sum(1 for r in filtered_reviews 
                                  if r.get('relevant', False) and self._should_filter_platform(r.get('platform', 'Unknown')))
            
            logger.info(f"Filtered {filtered_count} reviews: {relevant_filtered} relevant, "
                       f"{filtered_count - relevant_filtered} not relevant")
        
        logger.info(f"Total reviews: {len(filtered_reviews)}, Total relevant: {total_relevant}")
        
        return filtered_reviews


if __name__ == "__main__":
    """
    Test the RelevanceFilter with sample data.
    """
    print("Testing RelevanceFilter Module")
    
    # Sample test data
    test_reviews = [
        {"content": "IK course was great. The instructors were knowledgeable and helpful.", "platform": "Trustpilot"},
        {"content": "Interview Kickstart helped me land a job at a FAANG company.", "platform": "Trustpilot"},
        {"content": "This random review has nothing to do with Interview Kickstart.", "platform": "Reddit"},
        {"content": "IK is expensive but worth it for the career boost.", "platform": "Course Report"},
        {"content": "I like this product, it works well for cleaning.", "platform": "Amazon"},
        {"content": "The IK program is intensive but effective.", "platform": "Quora"},
        {"review_content": "Working with Ajita from Interview Kickstart has been a great experience.", "platform": "Trustpilot"},
        {"content": "## Company details\n\nInterview Kickstart is a part-time, 12-15 week online interview training platform.", "platform": "Trustpilot"},
    ]
    
    # Test with all platforms
    print("\nTest with all platforms:")
    filter_all = RelevanceFilter()
    filtered_all = filter_all.filter_reviews(test_reviews)
    
    # Print results
    for review in filtered_all:
        content = review.get('content', review.get('review_content', 'No content'))
        print(f"RELEVANT: {review.get('relevant', False)} - Platform: {review.get('platform', 'Unknown')}")
        print(f"Content: {content[:50]}...")
        print("-" * 50)
    
    # Test with specific platforms
    print("\nTest with only Trustpilot:")
    filter_trustpilot = RelevanceFilter(platforms_to_filter=["Trustpilot"])
    filtered_trustpilot = filter_trustpilot.filter_reviews(test_reviews)
    
    # Print results
    for review in filtered_trustpilot:
        content = review.get('content', review.get('review_content', 'No content'))
        print(f"RELEVANT: {review.get('relevant', False)} - Platform: {review.get('platform', 'Unknown')}")
        print(f"Content: {content[:50]}...")
        print("-" * 50) 