# Configuration module for the RALPh application.
# Handles environment variables and application settings.

import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
_ = load_dotenv(find_dotenv())

# API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_TOKEN")

# IRIS Database settings (with default DB config settings)
IRIS_USERNAME = os.environ.get("IRIS_USERNAME", "demo")
IRIS_PASSWORD = os.environ.get("IRIS_PASSWORD", "demo")
IRIS_HOSTNAME = os.environ.get("IRIS_HOSTNAME", "localhost")
IRIS_PORT = os.environ.get("IRIS_PORT", "1972")
IRIS_NAMESPACE = os.environ.get("IRIS_NAMESPACE", "USER")
IRIS_COLLECTION_NAME = os.environ.get("IRIS_COLLECTION_NAME", "ralph_drug_database")

# Create IRIS connection string
IRIS_CONNECTION_STRING = f"iris://{IRIS_USERNAME}:{IRIS_PASSWORD}@{IRIS_HOSTNAME}:{IRIS_PORT}/{IRIS_NAMESPACE}"

# Send Email settings
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.environ.get("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.environ.get("EMAIL_SMTP_PORT", "587"))

# Chat settings
MEMORY_CHAR_LIMIT = int(os.environ.get("MEMORY_CHAR_LIMIT", "1000"))

# Directories
LOG_DIR = "logging/logs"
SUMMARIES_DIR = "logging/summaries"
AUDIO_FILES_DIR = "logging/audiofiles"

# Ensure required directories exist
for directory in [LOG_DIR, SUMMARIES_DIR, AUDIO_FILES_DIR]:
    os.makedirs(directory, exist_ok=True)


# Default patient and prescription details for testing
PATIENT_DETAILS_EXAMPLE = """
'Name': 'Helen Lee',\n
'NRIC': 'S1099999F',\n
'Date of Birth: '9 August 1945',\n
'Gender': 'Female',\n
'Allergy': 'Paracetamol (Panadol)',\n
'Past medical history': 'Type 2 diabetes, High Cholesterol (Hypercholesteromeia)'\n
'Labs': 'HbA1c: 9.0, LDL: 2.2, eGFR: 60'\n
"""

PRESCRIPTION_DETAILS_EXAMPLE = """1. ATORVASTATIN 20mg tablets - 1 tablet once in the morning - NO CHANGE
2. EMPAGLIFLOZIN 25mg tablets - 1 tablet once in the morning - NEWLY PRESCRIBED DRUG"""
