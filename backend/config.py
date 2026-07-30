"""
config.py
----------
Centralized configuration for our Flask app.
Instead of scattering settings across files, we keep them here
so they're easy to find and change.
"""

import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()

class Config:
    # Secret key used by Flask for sessions/security (keep it random & private)
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-fallback-key")

    # Gemini API key — will be used starting Feature 2 (Q&A)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Where uploaded PDFs will be stored on disk
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")

    # SQLite database file path
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database", "app.db")

    # Max upload size: 10 MB (prevents huge file abuse)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024