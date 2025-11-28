import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from django.conf import settings
from xml.dom import minidom
from lxml import etree

def calcular_hash_sha256(texto):
    """
    Recibe un string (contenido del XML o datos) y devuelve su hash SHA-256.
    Equivalente a la clase ChecksumUtil de Java.
    """
    # Convertimos el texto a bytes (utf-8) porque hashlib trabaja con bytes
    data_bytes = texto.encode('utf-8')
    
    # Creamos el objeto hash SHA-256
    sha256 = hashlib.sha256()
    
    # Alimentamos el hash con los datos
    sha256.update(data_bytes)
    
    # Devolvemos el resultado en hexadecimal (la cadena de números y letras)
    return sha256.hexdigest()

def validar_xsd(xml_element_root, xsd_path):
    """Valida un objeto ElementTree contra un archivo XSD."""
    try:
        schema_doc = etree.parse(xsd_path)
        schema = etree.XMLSchema(schema_doc)
        
        # Convertir de xml.etree a lxml
        xml_string = ET.tostring(xml_element_root)
        doc = etree.fromstring(xml_string)
        
        schema.assertValid(doc)
        return True, "Estructura válida"
    except etree.DocumentInvalid as e:
        return False, f"Error de estructura XSD: {e}"
    except Exception as e:
        return False, f"Error interno validando: {e}"

def create_patient_xml_content(perfil_paciente):
    """
    Crea el contenido XML como un string, valida contra XSD, calcula el Checksum SHA-256 
    de los datos y lo inserta en la sección de metadatos.
    """
    usuario = perfil_paciente.id_usuario
    direccion = usuario.direccion
    
    # 1. Crear la estructura XML solo con los DATOS del paciente (el "XML ORIGINAL")
    root = ET.Element('paciente')
    
    # Número de afiliación
    ET.SubElement(root, 'num_afiliacion').text = perfil_paciente.num_afiliacion
    
    # Datos personales
    datos_personales = ET.SubElement(root, 'datos_personales')
    ET.SubElement(datos_personales, 'primer_nombre').text = usuario.primer_nombre
    ET.SubElement(datos_personales, 'segundo_nombre').text = usuario.segundo_nombre or ''
    ET.SubElement(datos_personales, 'primer_apellido').text = usuario.primer_apellido
    ET.SubElement(datos_personales, 'segundo_apellido').text = usuario.segundo_apellido or ''
    nombre_completo = f"{usuario.primer_nombre} {usuario.segundo_nombre or ''} {usuario.primer_apellido} {usuario.segundo_apellido or ''}".strip().replace('  ', ' ')
    ET.SubElement(datos_personales, 'nombre_completo').text = nombre_completo
    ET.SubElement(datos_personales, 'edad').text = str(usuario.edad)
    ET.SubElement(datos_personales, 'genero').text = usuario.genero
    
    # Datos médicos
    datos_medicos = ET.SubElement(root, 'datos_medicos')
    ET.SubElement(datos_medicos, 'tipo_sangre').text = perfil_paciente.tipo_sangre or ''
    ET.SubElement(datos_medicos, 'alergias').text = perfil_paciente.alergias or ''
    
    # Contacto
    contacto = ET.SubElement(root, 'contacto')
    ET.SubElement(contacto, 'email_usuario').text = usuario.email_usuario
    ET.SubElement(contacto, 'numero_telefono').text = usuario.numero_telefono
    
    # Dirección
    direccion_elem = ET.SubElement(root, 'direccion')
    if direccion:
        ET.SubElement(direccion_elem, 'calle').text = direccion.calle
        ET.SubElement(direccion_elem, 'num_ext').text = direccion.num_ext
        ET.SubElement(direccion_elem, 'num_int').text = direccion.num_int or ''
        ET.SubElement(direccion_elem, 'colonia').text = direccion.colonia
        ET.SubElement(direccion_elem, 'ciudad').text = direccion.ciudad
        ET.SubElement(direccion_elem, 'estado').text = str(direccion.estado.id_estado)
        ET.SubElement(direccion_elem, 'c_postal').text = direccion.c_postal

    # ==========================================
    # NUEVO: VALIDACIÓN XSD ANTES DE CHECKSUM
    # ==========================================
    xsd_path = os.path.join(settings.BASE_DIR, 'schemas', 'paciente.xsd')
    if os.path.exists(xsd_path):
        es_valido, mensaje = validar_xsd(root, xsd_path)
        if not es_valido:
            print(f"❌ Error: El XML del paciente no cumple el esquema XSD. {mensaje}")
            # Aquí puedes decidir si lanzar una excepción o solo loguear el error
            # raise ValueError(f"XML Inválido: {mensaje}")
    else:
        print(f"⚠️ Advertencia: No se encontró el esquema XSD en {xsd_path}")

    # 2.  CÁLCULO DEL CHECKSUM 
    
    # Convertir el XML (solo datos) a un string limpio para calcular el hash.
    core_xml_bytes = ET.tostring(root, encoding='utf-8')
    core_xml_string_for_hash = core_xml_bytes.decode('utf-8').strip()
    
    # Calcular el Checksum (SHA-256)
    checksum_calculado = calcular_hash_sha256(core_xml_string_for_hash)
    
    # 3. AÑADIR los Metadatos y el Checksum
    metadatos = ET.SubElement(root, 'metadatos')
    ET.SubElement(metadatos, 'origen').text = 'WEB'
    ET.SubElement(metadatos, 'fecha_evento').text = datetime.now().isoformat() + 'Z'
    ET.SubElement(metadatos, 'operacion').text = 'ALTA'
    
    # Inyectar el hash calculado
    ET.SubElement(metadatos, 'checksum').text = checksum_calculado
    
    # 4. Convertir la estructura final (root + metadatos) a string con formato
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    
    # Usamos tu lógica de formato original para el XML final
    return reparsed.toprettyxml(indent="    ", encoding=None).replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')