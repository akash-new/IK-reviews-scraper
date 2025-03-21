"""
Course Report Parser Module for IK Review Scraper.

This module provides functionality to parse reviews from Course Report HTML content.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

# Basic logging setup
logger = logging.getLogger(__name__)

class CourseReportParser:
    """Parser for Course Report reviews."""
    
    def __init__(self):
        """Initialize the Course Report parser."""
        pass
    
    def parse_reviews(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse reviews from Course Report HTML content.
        
        Args:
            html_content (str): HTML content from Course Report page.
            
        Returns:
            List[Dict[str, Any]]: List of parsed reviews.
        """
        reviews = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all review containers
        review_containers = soup.find_all('div', class_='review-container')
        
        if not review_containers:
            logger.warning("No review containers found in HTML content")
            logger.info("Trying to extract reviews from sample format")
            # Try alternative format
            review_containers = soup.find_all('div', class_='review')
        
        logger.info(f"Found {len(review_containers)} potential review blocks")
        
        for container in review_containers:
            try:
                review = {}
                
                # Extract reviewer name and description
                reviewer_section = container.find('div', class_='reviewer-info')
                if reviewer_section:
                    name_elem = reviewer_section.find('div', class_='name')
                    if not name_elem:
                        name_elem = reviewer_section.find('h3', class_='name')
                    review['reviewer_name'] = name_elem.get_text(strip=True) if name_elem else "Anonymous"
                    
                    desc_elem = reviewer_section.find('div', class_='description')
                    if not desc_elem:
                        desc_elem = reviewer_section.find('p', class_='description')
                    review['reviewer_description'] = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Extract review date
                date_elem = container.find('div', class_='date')
                if not date_elem:
                    date_elem = container.find('time', class_='date')
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    try:
                        # Parse date in format "MMM DD, YYYY"
                        review_date = datetime.strptime(date_text, "%b %d, %Y")
                        review['review_date'] = review_date.strftime("%Y-%m-%d")
                    except ValueError:
                        review['review_date'] = date_text
                
                # Extract review title
                title_elem = container.find('h3', class_='review-title')
                if not title_elem:
                    title_elem = container.find('h2', class_='review-title')
                review['review_title'] = title_elem.get_text(strip=True) if title_elem else ""
                
                # Extract ratings
                ratings_section = container.find('div', class_='ratings')
                if ratings_section:
                    # Overall experience rating
                    overall_rating = ratings_section.find('div', class_='overall-rating')
                    if overall_rating:
                        rating_value = overall_rating.find('div', class_='rating')
                        if not rating_value:
                            rating_value = overall_rating.find('span', class_='rating')
                        review['overall_experience_rating'] = float(rating_value.get_text(strip=True)) if rating_value else 0.0
                    
                    # Individual ratings
                    rating_categories = {
                        'Instructor': 'instructor_rating',
                        'Curriculum': 'curriculum_rating',
                        'Job Assistance': 'job_assistance_rating'
                    }
                    
                    for category, field in rating_categories.items():
                        rating_elem = ratings_section.find('div', string=re.compile(category, re.I))
                        if rating_elem:
                            rating_value = rating_elem.find_next('div', class_='rating')
                            if not rating_value:
                                rating_value = rating_elem.find_next('span', class_='rating')
                            review[field] = float(rating_value.get_text(strip=True)) if rating_value else 0.0
                
                # Extract review content
                content_elem = container.find('div', class_='review-content')
                if not content_elem:
                    content_elem = container.find('div', class_='content')
                review['review_content'] = content_elem.get_text(strip=True) if content_elem else ""
                
                # Add review if it has content
                if review.get('review_content') or review.get('review_title'):
                    reviews.append(review)
                
            except Exception as e:
                logger.error(f"Error parsing review: {str(e)}")
                continue
        
        logger.info(f"Successfully parsed {len(reviews)} reviews")
        return reviews
    
    @staticmethod
    def get_next_page_url(content: str) -> Optional[str]:
        """
        Extract the URL for the next page of reviews.
        
        Args:
            content (str): HTML content of the current page
            
        Returns:
            Optional[str]: URL for the next page, or None if there is no next page
        """
        try:
            # Look for pagination links
            soup = BeautifulSoup(content, 'html.parser')
            pagination = soup.find('ul', class_='pagination')
            
            if pagination:
                # Find the active page and look for the next one
                active_page = pagination.find('li', class_='active')
                if active_page and active_page.find_next_sibling('li'):
                    next_page = active_page.find_next_sibling('li')
                    next_link = next_page.find('a')
                    if next_link and 'href' in next_link.attrs:
                        return next_link['href']
                        
            # Alternative: look for "Next" or ">" links
            next_link = soup.find('a', string='Next') or soup.find('a', string='›') or soup.find('a', string='>')
            if next_link and 'href' in next_link.attrs:
                return next_link['href']
                
        except Exception as e:
            logger.error(f"Error finding next page URL: {str(e)}")
            
        return None 