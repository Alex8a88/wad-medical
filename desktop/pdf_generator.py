import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generar_pdf_receta_local(receta, medicamentos, output_path):
    """
    Genera el PDF de la receta usando los datos locales (SQLAlchemy objects).
    """
    # Crear carpeta si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=1*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                fontSize=18, spaceAfter=30, alignment=1)
    
    story = []
    story.append(Paragraph("RECETA MÉDICA (COPIA LOCAL)", title_style))
    story.append(Spacer(1, 20))
    
    # Datos de la receta (Adaptado para usar objetos, no diccionarios)
    info_data = [
        ['FOLIO WEB:', receta.folio_web],
        ['FECHA:', str(receta.fecha_creacion)],
        ['MÉDICO:', receta.nombre_doctor],
        ['CÉDULA:', receta.cedula_doctor],
        ['', ''],
        ['DIAGNÓSTICO:', receta.diagnostico],
        ['PACIENTE (Afiliación):', receta.num_afiliacion]
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
    
    # Tabla de Medicamentos
    story.append(Paragraph("MEDICAMENTOS", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    med_data = [['MEDICINA', 'DOSIS', 'FRECUENCIA', 'DURACIÓN', 'NOTAS']]
    
    for med in medicamentos:
        med_data.append([
            med.nombre_medicamento, 
            med.dosis, 
            med.frecuencia,
            med.duracion,
            med.notas
        ])
    
    # Ajustamos anchos para que quepan 5 columnas
    med_table = Table(med_data, colWidths=[1.8*inch, 1.2*inch, 1.5*inch, 1.2*inch, 1.3*inch])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10), # Letra un poco más chica para que quepa
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(med_table)
    
    # Firma del Doctor
    story.append(Spacer(1, 60))
    story.append(Paragraph("_" * 40, styles['Normal']))
    story.append(Paragraph(f"Dr. {receta.nombre_doctor}", styles['Normal']))
    story.append(Paragraph(f"Cédula: {receta.cedula_doctor}", styles['Normal']))
    
    doc.build(story)
    print(f"📄 PDF generado exitosamente: {output_path}")
    return output_path