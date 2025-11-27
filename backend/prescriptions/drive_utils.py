import os
import pickle
import mimetypes
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from django.conf import settings
from dotenv import load_dotenv

# Cargar entorno
env_path = os.path.join(settings.BASE_DIR, '.env')
load_dotenv(env_path, override=True)

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_drive_backend():
    """Autentica SIN abrir navegador (No bloqueante)."""
    creds = None
    token_path = os.path.join(settings.BASE_DIR, 'drive_token.pickle')
    
    # 1. Intentar cargar token existente
    if os.path.exists(token_path):
        try:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        except Exception:
            print("⚠️ El archivo de token está corrupto.")
            creds = None

    # 2. Validar credenciales
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Guardar token refrescado
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"❌ No se pudo refrescar el token: {e}")
                return None
        else:
            print("❌ ERROR: No hay token válido. Ejecuta 'auth_drive_manual.py' primero.")
            # IMPORTANTE: Ya no intentamos abrir el navegador aquí para no colgar el server
            return None

    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(local_filepath, filename):
    print(f"--- ☁️ Subiendo a Drive: {filename} ---")
    try:
        # 1. Obtener ID de Carpeta
        folder_id = os.getenv('DRIVE_FOLDER_ID')
        if not folder_id:
            print("❌ ERROR: Falta DRIVE_FOLDER_ID en .env")
            return None

        # 2. Autenticar
        service = authenticate_drive_backend()
        if not service:
            print("❌ ERROR: Falló autenticación. El archivo NO se subirá.")
            return None

        # 3. Subir
        file_metadata = {'name': filename, 'parents': [folder_id]}
        mime_type, _ = mimetypes.guess_type(local_filepath)
        if mime_type is None: mime_type = 'application/octet-stream'
        
        media = MediaFileUpload(local_filepath, mimetype=mime_type)
        
        file = service.files().create(
            body=file_metadata, media_body=media, fields='id'
        ).execute()
        
        print(f"✅ Subida exitosa. ID: {file.get('id')}")
        return file.get('id')

    except Exception as e:
        print(f"❌ Error en subida: {e}")
        return None

def upload_xml_to_drive(local_filepath, filename):
    return upload_file_to_drive(local_filepath, filename)