#!/usr/bin/env python3
"""
Script to check available Gemini models with the current API key.
This will help us diagnose which models are accessible.
"""

import os
import logging
from google.api_core.exceptions import GoogleAPIError

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Google Generative AI package is not installed")
    exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    # Get API key from environment variable
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("No Gemini API key found in environment variables")
        exit(1)
    
    logger.info(f"Using API key: {api_key[:4]}...{api_key[-4:]}")
    
    # Configure the genai module
    genai.configure(api_key=api_key)
    
    try:
        # List available models
        logger.info("Fetching available models...")
        models = genai.list_models()
        
        # Filter for models supported for text generation
        logger.info("Available models:")
        for model in models:
            logger.info(f"- {model.name}")
            logger.info(f"  Supported generation methods: {model.supported_generation_methods}")
    
    except GoogleAPIError as e:
        logger.error(f"Google API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 