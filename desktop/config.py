import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

# Legacy SQLite
DATABASE_URL = "sqlite:///recetas.db"

# --- GOOGLE DRIVE CONFIGURATION ---
# ¡OJO! Aquí debes poner los IDs que copiaste de las carpetas específicas

# 1. Carpeta de PACIENTES (Para sync_patients.py)
DRIVE_FOLDER_ID_PACIENTES = "1mNEOtJcX90E3N3WMi2knv8tiJ7x0Am93"
# 2. Carpeta de RECETAS (Para sync_prescriptions.py)
DRIVE_FOLDER_ID_RECETAS = "13Ui7y2TCeQCSbxRs1UlqS-v5X79snhyR"

APP_NAME = "AppRecetasDesktop"
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"