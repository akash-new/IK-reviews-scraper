# Google Sheets Credentials Setup

To enable storage of reviews in Google Sheets, you need to create a Google Cloud service account and obtain credentials. Follow these steps:

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on "Select a project" at the top of the page
3. Click "New Project"
4. Enter a name for your project and click "Create"

## 2. Enable the Google Sheets API

1. In your new project, go to "APIs & Services" > "Library"
2. Search for "Google Sheets API"
3. Click on it and then click "Enable"

## 3. Create a Service Account

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter a name and description for your service account
4. Click "Create and Continue"
5. In the "Grant this service account access to project" section, select "Editor" role
6. Click "Continue" and then "Done"

## 4. Generate a Key for the Service Account

1. In the Service Accounts list, find the service account you just created
2. Click on the three dots menu for that account and select "Manage keys"
3. Click "Add Key" > "Create new key"
4. Choose "JSON" as the key type
5. Click "Create"
6. The key will be downloaded to your computer as a JSON file

## 5. Use the Key in Your Application

1. Copy the content of the downloaded JSON file
2. Replace the content of your `credentials/google_sheets_credentials.json` file with this content

## 6. Share Your Google Sheet

For a new spreadsheet, the script will create it for you. If you're using an existing spreadsheet:

1. Get the spreadsheet ID (it's the long string in the URL between `/d/` and `/edit`)
2. Set this ID in your `config/storage_config.json` file
3. Share your spreadsheet with the service account email (found in the `client_email` field of your credentials file)

## Troubleshooting

- If you see "Error loading credentials", make sure your credentials file contains valid JSON data
- If you see "Permission denied", make sure you've shared your spreadsheet with the service account email
- If you need to regenerate credentials, repeat step 4 above and update your credentials file

For more information, see the [Google Sheets API documentation](https://developers.google.com/sheets/api/guides/concepts). 