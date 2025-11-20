import os
import base64
import string
import secrets
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from PyPDF2 import PdfWriter, PdfReader
from django.conf import settings

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def generar_password():
    """Genera una contraseña alfanumérica aleatoria de 16 caracteres"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))

def obtener_servicio_gmail():
    """Obtiene el servicio de Gmail API"""
    creds = None
    
    # Token file para Gmail
    token_path = os.path.join(settings.BASE_DIR, 'gmail_token.json')
    credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # Si no hay credenciales válidas, solicitar autorización
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guardar credenciales para próxima ejecución
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def crear_pdf_receta(receta_info):
    """Crea un PDF con la información de la receta"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                fontSize=18, spaceAfter=30, alignment=1)
    
    story = []
    story.append(Paragraph("RECETA MÉDICA", title_style))
    story.append(Spacer(1, 20))
    
    # Información del paciente y médico
    info_data = [
        ['PACIENTE:', receta_info['paciente_nombre']],
        ['EDAD:', str(receta_info.get('paciente_edad', 'N/A'))],
        ['GÉNERO:', receta_info.get('paciente_genero', 'N/A')],
        ['EMAIL:', receta_info.get('paciente_email', 'N/A')],
        ['', ''],
        ['MÉDICO:', receta_info['medico_nombre']],
        ['DIAGNÓSTICO:', receta_info['diagnostico']],
        ['FECHA:', str(receta_info['fecha_creacion'])]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 30))
    
    # Tabla de medicamentos
    story.append(Paragraph("MEDICAMENTOS PRESCRITOS", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    med_data = [['MEDICINA', 'DOSIS', 'FRECUENCIA']]
    for med in receta_info['medicamentos']:
        med_data.append([med['medicamento_nombre'], med['dosis'], med['frecuencia']])
    
    med_table = Table(med_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(med_table)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def proteger_pdf_con_password(pdf_bytes, password):
    """Protege un PDF con contraseña"""
    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
    pdf_writer = PdfWriter()
    
    for page in pdf_reader.pages:
        pdf_writer.add_page(page)
    
    pdf_writer.encrypt(password)
    
    output_buffer = io.BytesIO()
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer.getvalue()

def crear_mensaje_con_adjunto(destinatario, asunto, cuerpo, pdf_bytes, filename):
    """Crea un mensaje de email con adjunto PDF"""
    mensaje = MIMEMultipart()
    mensaje['to'] = destinatario
    mensaje['subject'] = asunto
    
    mensaje.attach(MIMEText(cuerpo, 'plain'))
    
    part = MIMEBase('application', 'pdf')
    part.set_payload(pdf_bytes)
    
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
    
    mensaje.attach(part)
    
    raw_message = base64.urlsafe_b64encode(mensaje.as_bytes()).decode()
    return {'raw': raw_message}

def enviar_email(destinatario, asunto, cuerpo, pdf_bytes=None, filename=None):
    """Envía email con o sin adjunto"""
    try:
        service = obtener_servicio_gmail()
        
        if pdf_bytes and filename:
            mensaje = crear_mensaje_con_adjunto(destinatario, asunto, cuerpo, pdf_bytes, filename)
        else:
            mensaje_simple = MIMEText(cuerpo)
            mensaje_simple['to'] = destinatario
            mensaje_simple['subject'] = asunto
            raw_message = base64.urlsafe_b64encode(mensaje_simple.as_bytes()).decode()
            mensaje = {'raw': raw_message}
        
        result = service.users().messages().send(userId='me', body=mensaje).execute()
        return True, f"Email enviado. ID: {result['id']}"
        
    except Exception as e:
        return False, f"Error enviando email: {str(e)}"

def registrar_envio_email(receta_id, destinatario, tipo_email, asunto, estado, mensaje_error=None):
    """Registra el intento de envío de email en la base de datos"""
    from .models import EnviosEmail, Receta
    try:
        receta = Receta.objects.get(id=receta_id)
        envio = EnviosEmail(
            receta=receta,
            destinatario=destinatario,
            tipo_email=tipo_email,
            asunto=asunto,
            estado=estado,
            mensaje_error=mensaje_error
        )
        envio.save()
    except Exception as e:
        print(f"Error registrando envío de email: {e}")

def enviar_receta_por_email(receta_info):
    """Envía la receta y contraseña por email"""
    email_paciente = receta_info.get('paciente_email')
    receta_id = receta_info['id']
    
    if not email_paciente:
        return False, "El paciente no tiene email registrado"
    
    # Generar contraseña
    password = generar_password()
    
    # Crear PDF
    pdf_bytes = crear_pdf_receta(receta_info)
    pdf_protegido = proteger_pdf_con_password(pdf_bytes, password)
    
    # Save PDF to pdfs folder for auditing
    pdf_folder = os.path.join(settings.BASE_DIR, 'pdfs')
    os.makedirs(pdf_folder, exist_ok=True)
    pdf_filename = f"receta_{receta_info['id']}_{receta_info['paciente_nombre'].replace(' ', '_')}.pdf"
    pdf_path = os.path.join(pdf_folder, pdf_filename)
    
    with open(pdf_path, 'wb') as f:
        f.write(pdf_protegido)
    print(f"PDF saved to: {pdf_path}")
    
    # Email con PDF
    filename = f"receta_{receta_info['id']}_{receta_info['paciente_nombre'].replace(' ', '_')}.pdf"
    asunto_pdf = f"Receta Médica - {receta_info['paciente_nombre']}"
    cuerpo_pdf = f"""Estimado/a {receta_info['paciente_nombre']},

Adjunto encontrará su receta médica en formato PDF.

Detalles de la receta:
- Médico: {receta_info['medico_nombre']}
- Diagnóstico: {receta_info['diagnostico']}
- Fecha: {receta_info['fecha_creacion']}

El archivo está protegido con contraseña por seguridad. Recibirá la contraseña en un email separado.

Saludos cordiales,
Sistema de Recetas Médicas"""
    
    # Email con contraseña
    asunto_password = f"Contraseña para Receta Médica - {receta_info['paciente_nombre']}"
    cuerpo_password = f"""Estimado/a {receta_info['paciente_nombre']},

La contraseña para abrir su receta médica es: {password}

Por favor, mantenga esta contraseña segura y no la comparta.

Saludos cordiales,
Sistema de Recetas Médicas"""
    
    # Enviar PDF
    success_pdf, msg_pdf = enviar_email(email_paciente, asunto_pdf, cuerpo_pdf, pdf_protegido, filename)
    if success_pdf:
        registrar_envio_email(receta_id, email_paciente, 'PDF', asunto_pdf, 'EXITOSO')
    else:
        registrar_envio_email(receta_id, email_paciente, 'PDF', asunto_pdf, 'ERROR', msg_pdf)
        return False, f"Error enviando PDF: {msg_pdf}"
    
    # Enviar contraseña
    success_pwd, msg_pwd = enviar_email(email_paciente, asunto_password, cuerpo_password)
    if success_pwd:
        registrar_envio_email(receta_id, email_paciente, 'PASSWORD', asunto_password, 'EXITOSO')
    else:
        registrar_envio_email(receta_id, email_paciente, 'PASSWORD', asunto_password, 'ERROR', msg_pwd)
        return False, f"Error enviando contraseña: {msg_pwd}"
    
    return True, f"Emails enviados correctamente a {email_paciente}"