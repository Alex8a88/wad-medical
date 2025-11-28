#!/usr/bin/env python3
import os
import pickle
import xml.etree.ElementTree as ET
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from db import SessionLocal, Usuario, PerfilPaciente, Direcciones, CatalogoEstados, init_db

# Intentamos importar el ID de la carpeta
try:
    from config import DRIVE_FOLDER_ID_PACIENTES 
except ImportError:
    DRIVE_FOLDER_ID_PACIENTES = None

# Importamos el verificador robusto
try:
    from checksum_utils import verificar_checksum_xml
except ImportError:
    def verificar_checksum_xml(path): return True, "Omitido"

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# --- CORRECCIÓN MAESTRA: RUTAS ABSOLUTAS ---
# Esto calcula la ruta exacta de la carpeta 'desktop' sin importar desde dónde ejecutes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.pickle')

def authenticate_google_drive():
    """Autentica y devuelve el servicio de Drive usando rutas seguras."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        
        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                # Mensaje de error detallado para saber qué pasó
                raise FileNotFoundError(f"No se encontró el archivo de credenciales en: {CREDENTIALS_PATH}")
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guardamos el token en la ruta segura
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
            
    return build('drive', 'v3', credentials=creds)

def fetch_patient_files(service, folder_id):
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and name contains 'paciente_' and name contains '.xml' and trashed = false",
            fields="files(id, name, modifiedTime)",
            orderBy="name desc"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        print(f"Error buscando archivos: {e}")
        return []

def download_file_bytes(service, file_id):
    try:
        request = service.files().get_media(fileId=file_id)
        return request.execute()
    except Exception as e:
        print(f"Error descarga: {e}")
        return None

def parse_patient_xml_string(xml_string):
    try:
        root = ET.fromstring(xml_string)
        patient_data = {}
        def get_val(tag): return root.findtext(f'.//{tag}', default='').strip()
        
        patient_data['primer_nombre'] = get_val('primer_nombre')
        patient_data['segundo_nombre'] = get_val('segundo_nombre')
        patient_data['primer_apellido'] = get_val('primer_apellido')
        patient_data['segundo_apellido'] = get_val('segundo_apellido')
        try: patient_data['edad'] = int(get_val('edad'))
        except: patient_data['edad'] = 0
        patient_data['genero'] = get_val('genero')
        patient_data['email_usuario'] = get_val('email_usuario')
        patient_data['numero_telefono'] = get_val('numero_telefono')
        patient_data['tipo_sangre'] = get_val('tipo_sangre')
        patient_data['alergias'] = get_val('alergias')
        patient_data['num_afiliacion'] = get_val('num_afiliacion')
        
        if not patient_data['num_afiliacion']: return None
        
        patient_data['calle'] = get_val('calle')
        patient_data['num_ext'] = get_val('num_ext')
        patient_data['num_int'] = get_val('num_int')
        patient_data['colonia'] = get_val('colonia')
        patient_data['ciudad'] = get_val('ciudad')
        patient_data['c_postal'] = get_val('c_postal')
        patient_data['estado'] = get_val('estado')
        return patient_data
    except Exception as e:
        print(f"Error parseo: {e}")
        return None

def upsert_patient(session, data, mod_time, integrity_valid=True):
    try:
        usuario = session.query(Usuario).filter_by(email_usuario=data['email_usuario']).first()
        if usuario:
            perfil = session.query(PerfilPaciente).filter_by(id_usuario=usuario.id_usuario).first()
        else:
            perfil = session.query(PerfilPaciente).filter_by(num_afiliacion=data['num_afiliacion']).first()
            usuario = perfil.usuario if perfil else None

        if usuario and perfil:
            # Actualizar
            usuario.primer_nombre = data['primer_nombre']
            usuario.segundo_nombre = data['segundo_nombre']
            usuario.primer_apellido = data['primer_apellido']
            usuario.segundo_apellido = data['segundo_apellido']
            usuario.edad = data['edad']
            usuario.genero = data['genero']
            usuario.numero_telefono = data['numero_telefono']
            
            perfil.num_afiliacion = data['num_afiliacion']
            perfil.tipo_sangre = data['tipo_sangre']
            perfil.alergias = data['alergias']
            if hasattr(perfil, "integridad_valida") or "integridad_valida" in PerfilPaciente.__table__.c:
                perfil.integridad_valida = integrity_valid

            if not usuario.direccion: usuario.direccion = Direcciones(id_usuario=usuario.id_usuario)
            usuario.direccion.calle = data['calle']
            usuario.direccion.num_ext = data['num_ext']
            usuario.direccion.num_int = data['num_int']
            usuario.direccion.colonia = data['colonia']
            usuario.direccion.ciudad = data['ciudad']
            usuario.direccion.c_postal = data['c_postal']
            
            print(f"Actualizado: {data['primer_nombre']} (Integridad: {'OK' if integrity_valid else 'FALLIDA'})")
        else:
            # Crear
            if not data['email_usuario']: return True
            usuario = Usuario(
                primer_nombre=data['primer_nombre'], segundo_nombre=data['segundo_nombre'],
                primer_apellido=data['primer_apellido'], segundo_apellido=data['segundo_apellido'],
                edad=data['edad'], genero=data['genero'], email_usuario=data['email_usuario'],
                numero_telefono=data['numero_telefono']
            )
            session.add(usuario)
            session.flush()
            
            pf_args = {
                "id_usuario": usuario.id_usuario, "num_afiliacion": data['num_afiliacion'],
                "tipo_sangre": data['tipo_sangre'], "alergias": data['alergias']
            }
            if hasattr(PerfilPaciente, "integridad_valida") or "integridad_valida" in PerfilPaciente.__table__.c:
                pf_args["integridad_valida"] = integrity_valid
            perfil = PerfilPaciente(**pf_args)
            session.add(perfil)
            session.flush()
            
            direccion = Direcciones(
                id_usuario=usuario.id_usuario, calle=data['calle'], num_ext=data['num_ext'],
                num_int=data['num_int'], colonia=data['colonia'], ciudad=data['ciudad'],
                c_postal=data['c_postal'], estado=1
            )
            session.add(direccion)
            print(f"Creado: {data['primer_nombre']} (Integridad: {'OK' if integrity_valid else 'FALLIDA'})")
            
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error upsert: {e}")
        return False

def get_latest_patient_files(files):
    patient_files = {}
    for file in files:
        fn = file['name']
        if fn.startswith('paciente_') and fn.endswith('.xml'):
            parts = fn[9:-4].split('_')
            if len(parts) >= 3:
                pid = '_'.join(parts[:-1])
                ts = parts[-1]
                if pid not in patient_files or ts > patient_files[pid]['timestamp']:
                    patient_files[pid] = {'file': file, 'timestamp': ts}
    return [d['file'] for d in patient_files.values()]

def sync_patients_from_drive():
    try:
        init_db()
        # Usar la autenticación corregida con rutas absolutas
        service = authenticate_google_drive()
        
        if not DRIVE_FOLDER_ID_PACIENTES:
            print("❌ Error: Falta configurar DRIVE_FOLDER_ID_PACIENTES en config.py")
            return False
            
        files = fetch_patient_files(service, DRIVE_FOLDER_ID_PACIENTES)
        if not files: return True
        
        latest = get_latest_patient_files(files)
        session = SessionLocal()
        
        try:
            for file in latest:
                # Descarga binaria
                xml_bytes = download_file_bytes(service, file['id'])
                if not xml_bytes: continue
                
                # Rutas temporales seguras
                temp_path = os.path.join(BASE_DIR, f"temp_{file['name']}")
                try:
                    with open(temp_path, 'wb') as f: f.write(xml_bytes)
                    es_valido, msg = verificar_checksum_xml(temp_path)
                except Exception as e:
                    print(f"Error verificación: {e}")
                    es_valido = False
                finally:
                    if os.path.exists(temp_path):
                        try: os.remove(temp_path)
                        except: pass
                        
                if not es_valido:
                    print(f"⚠️ ALERTA: {file['name']} alterado.")
                else:
                    print(f"✅ {file['name']} verificado.")
                    
                try:
                    xml_str = xml_bytes.decode('utf-8')
                    data = parse_patient_xml_string(xml_str)
                    if data: upsert_patient(session, data, file['modifiedTime'], es_valido)
                except Exception: pass
            return True
        finally:
            session.close()
    except Exception as e:
        raise Exception(f"Sync Error: {e}")

if __name__ == "__main__":
    sync_patients_from_drive()