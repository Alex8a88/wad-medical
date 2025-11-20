# drive_client.py - uses google API client (requires credentials.json and google libs installed)
import os, io, pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from config import CREDENTIALS_FILE, TOKEN_FILE, DRIVE_FOLDER_ID

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.metadata.readonly']

def obtener_servicio():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                # Delete expired token and re-authenticate
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('drive', 'v3', credentials=creds)
    return service

def subir_archivo_bytes(service, file_bytes, filename, folder_id=DRIVE_FOLDER_ID, mime_type='application/xml'):
    file_metadata = {'name': filename, 'parents': [folder_id]}
    fh = io.BytesIO(file_bytes)
    media = MediaIoBaseUpload(fh, mimetype=mime_type)
    file = service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
    return file

def listar_archivos_en_carpeta(service, folder_id=DRIVE_FOLDER_ID):
    query = f"'{folder_id}' in parents and mimeType='application/xml'"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name, createdTime)').execute()
    return results.get('files', [])

def descargar_archivo(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh.read()
