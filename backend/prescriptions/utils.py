import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from django.conf import settings
from xml.dom import minidom

def calcular_hash_sha256(texto):
    """Calcula el hash SHA-256 de un string."""
    if not texto: return ""
    data_bytes = texto.encode('utf-8')
    sha256 = hashlib.sha256()
    sha256.update(data_bytes)
    return sha256.hexdigest()

def create_prescription_xml(receta):
    """
    Genera el archivo XML para una receta y lo guarda.
    """
    try:
        # Generar contenido
        xml_content = create_prescription_xml_content(receta)
        
        # Nombre del archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Intentar obtener afiliación de forma segura
        try:
            # CORRECCIÓN PRINCIPAL: Acceder a través del usuario
            if hasattr(receta.paciente, 'perfil_paciente'):
                num_afiliacion = receta.paciente.perfil_paciente.num_afiliacion
            else:
                num_afiliacion = "SIN_PERFIL"
        except Exception:
            num_afiliacion = "ERROR_AFILIACION"

        filename = f"receta_{num_afiliacion}_{timestamp}.xml"
        
        # Guardar en carpeta
        xml_folder = os.path.join(settings.BASE_DIR, 'xml_files')
        os.makedirs(xml_folder, exist_ok=True)
        filepath = os.path.join(xml_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as archivo:
            archivo.write(xml_content)
        
        return filepath
    except Exception as e:
        print(f"❌ Error creando archivo XML: {e}")
        # Retornamos None para que la vista sepa que falló pero no explote
        return None

def create_prescription_xml_content(receta):
    """
    Crea la estructura XML de la receta.
    """
    root = ET.Element('receta')
    
    # --- 1. CABECERA ---
    try:
        ET.SubElement(root, 'folio').text = str(receta.id)
        fecha = receta.fecha_creacion.isoformat() if receta.fecha_creacion else datetime.now().isoformat()
        ET.SubElement(root, 'fecha_creacion').text = fecha
    except:
        ET.SubElement(root, 'folio').text = "0"

    # --- 2. PACIENTE ---
    paciente = ET.SubElement(root, 'paciente')
    try:
        usuario = receta.paciente
        # CORRECCIÓN: Verificar si existe el perfil antes de acceder
        if hasattr(usuario, 'perfil_paciente'):
            perfil = usuario.perfil_paciente
            ET.SubElement(paciente, 'num_afiliacion').text = str(perfil.num_afiliacion)
        else:
            ET.SubElement(paciente, 'num_afiliacion').text = "00000000"
            
        ET.SubElement(paciente, 'nombre_completo').text = f"{usuario.primer_nombre} {usuario.primer_apellido}"
    except Exception:
        ET.SubElement(paciente, 'num_afiliacion').text = "ERROR"
        ET.SubElement(paciente, 'nombre_completo').text = "Desconocido"

    # --- 3. DOCTOR ---
    doctor_elem = ET.SubElement(root, 'doctor')
    try:
        medico = receta.medico
        if medico:
            usuario_medico = medico.id_usuario
            ET.SubElement(doctor_elem, 'cedula').text = str(medico.cedula_profesional)
            ET.SubElement(doctor_elem, 'nombre').text = f"{usuario_medico.primer_nombre} {usuario_medico.primer_apellido}"
        else:
            ET.SubElement(doctor_elem, 'cedula').text = "000000"
            ET.SubElement(doctor_elem, 'nombre').text = "Sin Medico"
    except Exception:
        ET.SubElement(doctor_elem, 'cedula').text = "ERROR"
        ET.SubElement(doctor_elem, 'nombre').text = "Error Medico"

    # --- 4. DIAGNÓSTICO ---
    ET.SubElement(root, 'diagnostico').text = str(receta.diagnostico or "")

    # --- 5. MEDICAMENTOS ---
    medicamentos_elem = ET.SubElement(root, 'medicamentos')
    try:
        # Intentamos obtener la relación de medicamentos de forma segura
        relacion = None
        if hasattr(receta, 'medicamentos'):
            relacion = receta.medicamentos
        elif hasattr(receta, 'recetamedicamento_set'):
            relacion = receta.recetamedicamento_set
            
        if relacion:
            for item in relacion.all(): 
                med = ET.SubElement(medicamentos_elem, 'medicamento')
                
                # Nombre del medicamento
                nombre = "Desconocido"
                if hasattr(item, 'medicamento'):
                    nombre = getattr(item.medicamento, 'nombre_comercial', getattr(item.medicamento, 'nombre', 'Desconocido'))
                
                ET.SubElement(med, 'nombre').text = str(nombre)
                ET.SubElement(med, 'dosis').text = str(getattr(item, 'dosis', ''))
                ET.SubElement(med, 'frecuencia').text = str(getattr(item, 'frecuencia', ''))
                
                # Campos opcionales
                if hasattr(item, 'duracion'):
                    ET.SubElement(med, 'duracion').text = str(item.duracion)
                if hasattr(item, 'notas'):
                    ET.SubElement(med, 'notas').text = str(item.notas or "")
    except Exception as e:
        print(f"⚠️ Error en medicamentos: {e}")

    # --- 6. CHECKSUM Y FINALIZACIÓN ---
    try:
        # Convertir a bytes y calcular hash sobre datos crudos
        core_xml_bytes = ET.tostring(root, encoding='utf-8')
        core_xml_string_for_hash = core_xml_bytes.decode('utf-8').strip()
        checksum_calculado = calcular_hash_sha256(core_xml_string_for_hash)

        # Agregar metadatos
        metadatos = ET.SubElement(root, 'metadatos')
        ET.SubElement(metadatos, 'origen').text = 'WEB_BACKEND'
        ET.SubElement(metadatos, 'operacion').text = 'NUEVA_RECETA'
        ET.SubElement(metadatos, 'checksum').text = checksum_calculado

        # Pretty Print
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ", encoding=None).replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')
        
    except Exception as e:
        print(f"❌ Error generando string final: {e}")
        return "<xml>ErrorGeneracion</xml>"