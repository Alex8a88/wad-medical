import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from db import SessionLocal, EnviosEmail

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def obtener_servicio_gmail():
    """Obtiene el servicio de Gmail API"""
    creds = None
    
    # Token file para Gmail
    if os.path.exists('gmail_token.json'):
        creds = Credentials.from_authorized_user_file('gmail_token.json', SCOPES)
    
    # Si no hay credenciales válidas, solicitar autorización
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refrescando token: {e}")
                # Si falla el refresh, eliminar token y reautorizar
                if os.path.exists('gmail_token.json'):
                    os.remove('gmail_token.json')
                creds = None
        
        if not creds or not creds.valid:
            # Usar el mismo archivo credentials.json que Drive
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Archivo credentials.json no encontrado. Descárgalo desde Google Cloud Console.")
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guardar credenciales para próxima ejecución
        with open('gmail_token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def crear_mensaje_con_adjunto(destinatario, asunto, cuerpo, archivo_path):
    """Crea un mensaje de email con adjunto PDF"""
    mensaje = MIMEMultipart()
    mensaje['to'] = destinatario
    mensaje['subject'] = asunto
    
    # Cuerpo del mensaje
    mensaje.attach(MIMEText(cuerpo, 'plain'))
    
    # Adjunto PDF
    with open(archivo_path, "rb") as attachment:
        part = MIMEBase('application', 'pdf')
        part.set_payload(attachment.read())
    
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename="{os.path.basename(archivo_path)}"'
    )
    
    mensaje.attach(part)
    
    # Codificar mensaje
    raw_message = base64.urlsafe_b64encode(mensaje.as_bytes()).decode()
    return {'raw': raw_message}

def registrar_envio_email(receta_id, destinatario, tipo_email, asunto, estado, mensaje_error=None):
    """Registra el intento de envío de email en la base de datos"""
    session = SessionLocal()
    try:
        envio = EnviosEmail(
            receta=receta_id,
            destinatario=destinatario,
            tipo_email=tipo_email,
            asunto=asunto,
            estado=estado,
            mensaje_error=mensaje_error
        )
        session.add(envio)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error registrando envío de email: {e}")
    finally:
        session.close()

def enviar_email(destinatario, asunto, cuerpo, archivo_path=None, receta_id=None, tipo_email='PDF'):
    """Envía email con o sin adjunto y registra el intento"""
    try:
        service = obtener_servicio_gmail()
        
        if archivo_path:
            mensaje = crear_mensaje_con_adjunto(destinatario, asunto, cuerpo, archivo_path)
        else:
            mensaje_simple = MIMEText(cuerpo)
            mensaje_simple['to'] = destinatario
            mensaje_simple['subject'] = asunto
            raw_message = base64.urlsafe_b64encode(mensaje_simple.as_bytes()).decode()
            mensaje = {'raw': raw_message}
        
        result = service.users().messages().send(userId='me', body=mensaje).execute()
        
        # Registrar envío exitoso
        if receta_id:
            registrar_envio_email(receta_id, destinatario, tipo_email, asunto, 'EXITOSO')
        
        return True, f"Email enviado. ID: {result['id']}"
        
    except Exception as e:
        error_msg = f"Error enviando email: {str(e)}"
        
        # Registrar envío fallido
        if receta_id:
            registrar_envio_email(receta_id, destinatario, tipo_email, asunto, 'ERROR', error_msg)
        
        return False, error_msg

def limpiar_pdf(pdf_path):
    """Elimina el archivo PDF después del envío"""
    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            return True, f"PDF eliminado: {pdf_path}"
        return False, "Archivo no encontrado"
    except Exception as e:
        return False, f"Error eliminando PDF: {str(e)}"

def enviar_receta_por_email(receta_info, pdf_path, password):
    """Envía la receta y contraseña por email, luego elimina el PDF"""
    email_paciente = receta_info['paciente']['correo']
    receta_id = receta_info['id']
    paciente_nombre = f"{receta_info['paciente']['nombre']} {receta_info['paciente']['primer_apellido']}"
    
    if not email_paciente:
        return False, "El paciente no tiene email registrado"
    
    # Verificar que el PDF existe
    if not os.path.exists(pdf_path):
        return False, f"Archivo PDF no encontrado: {pdf_path}"
    
    # Email con PDF
    asunto_pdf = f"Receta Médica - {paciente_nombre}"
    cuerpo_pdf = f"""Estimado/a {paciente_nombre},

Adjunto encontrará su receta médica en formato PDF.

Detalles de la receta:
- Médico: {receta_info['medico']['nombre']}
- Diagnóstico: {receta_info['diagnostico']}
- Fecha: {receta_info['fecha']}

El archivo está protegido con contraseña por seguridad. Recibirá la contraseña en un email separado.

Saludos cordiales,
Sistema de Recetas Médicas"""
    
    # Email con contraseña
    asunto_password = f"Contraseña para Receta Médica - {paciente_nombre}"
    cuerpo_password = f"""Estimado/a {paciente_nombre},

La contraseña para abrir su receta médica es: {password}

Por favor, mantenga esta contraseña segura y no la comparta.

Saludos cordiales,
Sistema de Recetas Médicas"""
    
    # Enviar PDF
    success_pdf, msg_pdf = enviar_email(email_paciente, asunto_pdf, cuerpo_pdf, pdf_path, receta_id, 'PDF')
    if not success_pdf:
        return False, f"Error enviando PDF: {msg_pdf}"
    
    # Enviar contraseña
    success_pwd, msg_pwd = enviar_email(email_paciente, asunto_password, cuerpo_password, None, receta_id, 'PASSWORD')
    if not success_pwd:
        return False, f"Error enviando contraseña: {msg_pwd}"
    
    # Limpiar PDF después del envío exitoso
    cleanup_success, cleanup_msg = limpiar_pdf(pdf_path)
    
    return True, f"Emails enviados correctamente a {email_paciente}. {cleanup_msg}"