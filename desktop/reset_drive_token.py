import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Definimos los permisos necesarios (Lectura y Escritura)
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly'
]

def reset_and_auth():
    print("--- 🔑 Renovación de Credenciales de Drive ---")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(base_dir, 'token.pickle')
    creds_path = os.path.join(base_dir, 'credentials.json')
    
    # 1. Eliminar token viejo
    if os.path.exists(token_path):
        try:
            os.remove(token_path)
            print("🗑️ Token antiguo eliminado.")
        except Exception as e:
            print(f"❌ Error borrando token: {e}")
            return

    # 2. Verificar credentials.json
    if not os.path.exists(creds_path):
        print(f"❌ ERROR: No se encontró '{creds_path}'")
        print("   Por favor copia el archivo credentials.json a la carpeta desktop.")
        return

    # 3. Iniciar nuevo Login
    print("\n🚀 Iniciando nuevo inicio de sesión...")
    print("   Se abrirá tu navegador. Por favor autoriza la aplicación.")
    print("   Asegúrate de marcar TODAS las casillas de permisos que pida Google.")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # 4. Guardar nuevo token
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
            
        print(f"\n✅ ¡ÉXITO! Nuevo token generado y guardado en: {token_path}")
        print("   Ahora tu aplicación tiene permisos de ESCRITURA y LECTURA.")
        
    except Exception as e:
        print(f"\n❌ Falló la autenticación: {e}")

if __name__ == "__main__":
    reset_and_auth()