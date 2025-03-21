#!/usr/bin/env python3
"""
Simple script to extract the service account email from Google Sheets credentials file.
"""

import json
import os
import sys

def main():
    """
    Extract and print the service account email from credentials file.
    """
    credentials_path = "credentials/google_sheets_credentials.json"
    
    # Check if the credentials file exists
    if not os.path.exists(credentials_path):
        print(f"Error: Credentials file not found: {credentials_path}")
        return
    
    # Read the credentials file
    try:
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in credentials file")
        return
    except Exception as e:
        print(f"Error reading credentials file: {e}")
        return
    
    # Extract the service account email
    client_email = credentials.get('client_email')
    if not client_email:
        print("Error: 'client_email' not found in credentials file")
        return
    
    # Print the email
    print("\nService Account Email:")
    print("======================")
    print(client_email)
    print("\nTo fix Google Sheets permission issues:")
    print("1. Go to your Google Sheets document")
    print("2. Click the 'Share' button in the top right")
    print("3. Enter this email address")
    print("4. Select 'Editor' permissions")
    print("5. Click 'Share'")
    print("\nAfter sharing, try running your script again with the --storage flag.")

if __name__ == "__main__":
    main() 