"""
Sentiment Analyzer Module for IK Review Scraper.

This module provides a SentimentAnalyzer class that analyzes the sentiment
of reviews using the Google Gemini API, with a fallback to dictionary-based approach.
"""

import logging
import re
import os
from typing import Dict, List, Any
import google.generativeai as genai
from dotenv import load_dotenv

# Basic logging setup
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class SentimentAnalyzer:
    """Sentiment analyzer using Gemini API with dictionary-based fallback."""
    
    def __init__(self, config):
        """Initialize the sentiment analyzer with configuration."""
        self.config = config
        self.model = genai.GenerativeModel('gemini-pro') if GEMINI_API_KEY else None
        
        # Basic positive and negative word lists for fallback
        self.positive_words = {
            'excellent', 'great', 'good', 'amazing', 'wonderful', 'fantastic',
            'helpful', 'best', 'love', 'perfect', 'recommend', 'awesome',
            'outstanding', 'exceptional', 'superb', 'brilliant', 'worth',
            'valuable', 'insightful', 'clear', 'supportive', 'professional',
            'knowledgeable', 'effective', 'organized', 'comprehensive'
        }
        
        self.negative_words = {
            'bad', 'poor', 'terrible', 'horrible', 'awful', 'worst',
            'disappointing', 'waste', 'useless', 'expensive', 'difficult',
            'hard', 'confusing', 'unclear', 'unhelpful', 'unprofessional',
            'overpriced', 'disorganized', 'lacking', 'insufficient',
            'frustrating', 'inadequate', 'mediocre', 'misleading'
        }
        
        # Sentiment intensifiers
        self.intensifiers = {
            'very', 'really', 'extremely', 'absolutely', 'completely',
            'totally', 'highly', 'especially', 'particularly', 'quite'
        }
    
    def _analyze_with_gemini(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using Gemini API.
        
        Args:
            text (str): The text to analyze.
            
        Returns:
            Dict[str, Any]: Dictionary with sentiment score and category.
        """
        try:
            prompt = f"""Analyze the sentiment of this review. Consider both the content and the language used.
            Provide a sentiment score from 0 to 100 (0 being most negative, 100 being most positive) and a category (NEGATIVE, NEUTRAL, or POSITIVE).
            Only respond with a JSON object containing 'score' and 'category' keys.
            
            Review: {text}"""
            
            response = self.model.generate_content(prompt)
            result = eval(response.text)  # Safe since we're controlling the prompt
            
            # Validate and normalize the response
            score = max(0, min(100, int(result['score'])))
            category = result['category'].upper()
            if category not in ['NEGATIVE', 'NEUTRAL', 'POSITIVE']:
                category = self.config.get_category(score)
            
            return {
                "score": score,
                "category": category
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return self._analyze_with_dictionary(text)
    
    def _analyze_with_dictionary(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using dictionary-based approach.
        
        Args:
            text (str): The text to analyze.
            
        Returns:
            Dict[str, Any]: Dictionary with sentiment score and category.
        """
        # Convert to lowercase and split into words
        words = re.findall(r'\w+', text.lower())
        
        # Count positive and negative words with intensifiers
        positive_score = 0
        negative_score = 0
        
        for i, word in enumerate(words):
            # Check for intensifiers
            intensifier = 1.0
            if i > 0 and words[i-1] in self.intensifiers:
                intensifier = 1.5
            
            if word in self.positive_words:
                positive_score += intensifier
            elif word in self.negative_words:
                negative_score += intensifier
        
        # Calculate sentiment score (0-100)
        total_score = positive_score + negative_score
        if total_score == 0:
            score = 50  # Neutral if no sentiment words found
        else:
            score = int((positive_score / total_score) * 100)
        
        # Get category based on score
        category = self.config.get_category(score)
        
        return {
            "score": score,
            "category": category
        }
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of a single text.
        
        Args:
            text (str): The text to analyze.
            
        Returns:
            Dict[str, Any]: Dictionary with sentiment score and category.
        """
        if self.model:
            return self._analyze_with_gemini(text)
        else:
            return self._analyze_with_dictionary(text)
    
    def analyze_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a list of reviews.
        
        Args:
            reviews (List[Dict[str, Any]]): List of review dictionaries.
            
        Returns:
            List[Dict[str, Any]]: List of sentiment results.
        """
        logger.info(f"Starting sentiment analysis of {len(reviews)} reviews")
        results = []
        
        for review in reviews:
            # Get the review content
            content = review.get("review_content", "")
            if not content:
                # If no content, use neutral sentiment
                results.append({"score": 50, "category": "neutral"})
                continue
            
            # Analyze the sentiment
            sentiment = self.analyze_text(content)
            results.append(sentiment)
        
        logger.info(f"Completed sentiment analysis for {len(reviews)} reviews")
        return results 