# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

# Legacy SQLite (for migration reference)
DATABASE_URL = "sqlite:///recetas.db"

# Google Drive Configuration
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "1mNEOtJcX90E3N3WMi2knv8tiJ7x0Am93")
APP_NAME = "AppRecetasDesktop"
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"
