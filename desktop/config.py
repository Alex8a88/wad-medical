import os
from dotenv import load_dotenv

# --- TRUCO DE MAGIA: RUTAS ABSOLUTAS ---
# Esto calcula la ruta real de la carpeta 'desktop' en tu disco duro
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

# Legacy SQLite
# Usamos la ruta absoluta también para la base de datos
db_path = os.path.join(BASE_DIR, "recetas.db")
DATABASE_URL = f"sqlite:///{db_path}"

# --- GOOGLE DRIVE CONFIGURATION ---

# ID de la carpeta PACIENTES
DRIVE_FOLDER_ID_PACIENTES = "1mNEOtJcX90E3N3WMi2knv8tiJ7x0Am93"

# ID de la carpeta RECETAS
DRIVE_FOLDER_ID_RECETAS = "1KQ-W6Glmj7vjnfLW9DxhNmLnx2aaNxrF"

APP_NAME = "AppRecetasDesktop"

# --- RUTAS DE CREDENCIALES ---
# Usamos os.path.join para construir la ruta completa y segura
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.pickle")