import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from django.conf import settings
from xml.dom import minidom
from lxml import etree

def calcular_hash_sha256(texto):
    if not texto: return ""
    data_bytes = texto.encode('utf-8')
    sha256 = hashlib.sha256()
    sha256.update(data_bytes)
    return sha256.hexdigest()

def validar_xsd(xml_element_root, xsd_path):
    """Valida la estructura XML contra el esquema XSD."""
    try:
        if not os.path.exists(xsd_path):
            return False, f"No se encontró el archivo XSD en: {xsd_path}"

        schema_doc = etree.parse(xsd_path)
        schema = etree.XMLSchema(schema_doc)
        
        xml_string = ET.tostring(xml_element_root)
        doc = etree.fromstring(xml_string)
        
        schema.assertValid(doc)
        return True, "Estructura válida"
    except etree.DocumentInvalid as e:
        return False, f"Error XSD: {e}"
    except Exception as e:
        return False, f"Error validando: {e}"

def create_prescription_xml(receta):
    try:
        # 1. Generar contenido (esto ejecutará la validación interna)
        xml_content = create_prescription_xml_content(receta)
        
        # Si la línea de arriba falló (por XSD), el código se detiene aquí.
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            if hasattr(receta.paciente, 'perfil_paciente'):
                num_afiliacion = receta.paciente.perfil_paciente.num_afiliacion
            else:
                num_afiliacion = "SIN_PERFIL"
        except:
            num_afiliacion = "ERROR"

        filename = f"receta_{num_afiliacion}_{timestamp}.xml"
        
        xml_folder = os.path.join(settings.BASE_DIR, 'xml_files')
        os.makedirs(xml_folder, exist_ok=True)
        filepath = os.path.join(xml_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return filepath
    except Exception as e:
        # Re-lanzamos la excepción para que la vista sepa que falló y muestre error 400
        print(f"❌ Error fatal creando XML: {e}")
        raise e

def create_prescription_xml_content(receta):
    root = ET.Element('receta')
    
    # --- DATOS ---
    try:
        ET.SubElement(root, 'folio').text = str(receta.id)
        fecha = receta.fecha_creacion.isoformat() if receta.fecha_creacion else datetime.now().isoformat()
        ET.SubElement(root, 'fecha_creacion').text = fecha
    except:
        ET.SubElement(root, 'folio').text = "0"

    paciente = ET.SubElement(root, 'paciente')
    try:
        u = receta.paciente
        p = getattr(u, 'perfil_paciente', None)
        ET.SubElement(paciente, 'num_afiliacion').text = p.num_afiliacion if p else "0000"
        ET.SubElement(paciente, 'nombre_completo').text = f"{u.primer_nombre} {u.primer_apellido}"
    except:
        ET.SubElement(paciente, 'nombre_completo').text = "Error Datos"

    doctor = ET.SubElement(root, 'doctor')
    try:
        m = receta.medico
        if m:
            u_m = m.id_usuario
            ET.SubElement(doctor, 'cedula').text = m.cedula_profesional
            ET.SubElement(doctor, 'nombre').text = f"{u_m.primer_nombre} {u_m.primer_apellido}"
        else:
            ET.SubElement(doctor, 'cedula').text = "0000"
            ET.SubElement(doctor, 'nombre').text = "Sin Medico"
    except:
        ET.SubElement(doctor, 'nombre').text = "Doctor"

    ET.SubElement(root, 'diagnostico').text = receta.diagnostico or ""

    medicamentos = ET.SubElement(root, 'medicamentos')
    meds = getattr(receta, 'medicamentos', None) or getattr(receta, 'recetamedicamento_set', None)
    
    if meds:
        for item in meds.all():
            m_elem = ET.SubElement(medicamentos, 'medicamento')
            nombre_med = "Desconocido"
            if hasattr(item, 'medicamento'):
                nombre_med = getattr(item.medicamento, 'nombre_comercial', getattr(item.medicamento, 'nombre', 'Desconocido'))
            
            ET.SubElement(m_elem, 'nombre').text = str(nombre_med)
            ET.SubElement(m_elem, 'dosis').text = str(getattr(item, 'dosis', ''))
            ET.SubElement(m_elem, 'frecuencia').text = str(getattr(item, 'frecuencia', ''))
            
            # Campos opcionales (minOccurs=0 en XSD)
            ET.SubElement(m_elem, 'duracion').text = str(getattr(item, 'duracion', 'N/A'))
            ET.SubElement(m_elem, 'notas').text = str(getattr(item, 'notas', ''))

    # ==========================================
    # 🚨 VALIDACIÓN XSD ESTRICTA
    # ==========================================
    xsd_path = os.path.join(settings.BASE_DIR, 'schemas', 'receta.xsd')
    es_valido, mensaje = validar_xsd(root, xsd_path)
    
    if not es_valido:
        # ESTO ES LO QUE LO HACE ESTRICTO:
        print(f"⛔ BLOQUEO DE SEGURIDAD: El XML no cumple el XSD.")
        print(f"   Razón: {mensaje}")
        raise ValueError(f"XML Inválido (XSD): {mensaje}") # Detiene el proceso
    
    print("✅ XML Receta validado correctamente.")

    # --- FIN ---
    raw_bytes = ET.tostring(root, encoding='utf-8')
    checksum = calcular_hash_sha256(raw_bytes.decode('utf-8').strip())

    metadatos = ET.SubElement(root, 'metadatos')
    ET.SubElement(metadatos, 'origen').text = 'WEB_BACKEND'
    ET.SubElement(metadatos, 'operacion').text = 'NUEVA_RECETA'
    ET.SubElement(metadatos, 'checksum').text = checksum

    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ", encoding=None).replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')