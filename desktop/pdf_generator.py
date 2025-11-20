import os
import string
import secrets
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from PyPDF2 import PdfWriter, PdfReader
import io

def generar_password():
    """Genera una contraseña alfanumérica aleatoria de 16 caracteres"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))

def crear_pdf_receta(receta_info):
    """Crea un PDF con la información de la receta"""
    # Crear buffer en memoria
    buffer = io.BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                fontSize=18, spaceAfter=30, alignment=1)
    
    # Contenido del PDF
    story = []
    
    # Título
    story.append(Paragraph("RECETA MÉDICA", title_style))
    story.append(Spacer(1, 20))
    
    # Información del paciente y médico
    info_data = [
        ['PACIENTE:', receta_info['paciente']['nombre']],
        ['EDAD:', str(receta_info['paciente']['edad']) if receta_info['paciente']['edad'] else 'N/A'],
        ['GÉNERO:', receta_info['paciente']['genero'] or 'N/A'],
        ['EMAIL:', receta_info['paciente']['correo'] or 'N/A'],
        ['', ''],
        ['MÉDICO:', receta_info['medico']['nombre']],
        ['CÉDULA:', receta_info['medico']['cedula'] or 'N/A'],
        ['DIAGNÓSTICO:', receta_info['diagnostico'] or 'N/A'],
        ['FECHA:', str(receta_info['fecha']) if receta_info['fecha'] else 'N/A']
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
        med_data.append([med['medicina'], med['dosis'], med['frecuencia']])
    
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
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def proteger_pdf_con_password(pdf_bytes, password):
    """Protege un PDF con contraseña"""
    # Leer PDF desde bytes
    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
    pdf_writer = PdfWriter()
    
    # Copiar páginas
    for page in pdf_reader.pages:
        pdf_writer.add_page(page)
    
    # Agregar contraseña
    pdf_writer.encrypt(password)
    
    # Escribir a buffer
    output_buffer = io.BytesIO()
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer.getvalue()

def generar_pdf_receta_completo(receta_info):
    """Genera PDF completo con contraseña y lo guarda"""
    # Generar contraseña
    password = generar_password()
    
    # Crear PDF
    pdf_bytes = crear_pdf_receta(receta_info)
    
    # Proteger con contraseña
    pdf_protegido = proteger_pdf_con_password(pdf_bytes, password)
    
    # Guardar archivo
    filename = f"receta_{receta_info['id']}_{receta_info['paciente']['nombre'].replace(' ', '_')}.pdf"
    filepath = os.path.join('pdfs', filename)
    
    with open(filepath, 'wb') as f:
        f.write(pdf_protegido)
    
    return filepath, password