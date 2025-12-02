import os
import xml.etree.ElementTree as ET
from datetime import datetime
from lxml import etree
from xml.dom import minidom
from db import SessionLocal
from db_recetas_models import RecetaLocal, MedicamentoRecetaLocal
from config import DRIVE_FOLDER_ID_RECETAS
from drive_client import subir_archivo_bytes, obtener_servicio
from checksum_utils import calcular_hash_sha256

def validar_xsd_receta(xml_root):
    """Valida la estructura de la receta contra receta.xsd"""
    try:
        # Busca el XSD relativo a este archivo
        base_dir = os.path.dirname(os.path.abspath(__file__))
        xsd_path = os.path.join(base_dir, 'schemas', 'receta.xsd')
        
        if not os.path.exists(xsd_path):
            return False, f"No se encontró el esquema XSD en {xsd_path}"

        schema_doc = etree.parse(xsd_path)
        schema = etree.XMLSchema(schema_doc)
        
        xml_str = ET.tostring(xml_root)
        doc = etree.fromstring(xml_str)
        
        schema.assertValid(doc)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def procesar_nueva_receta_local(datos_ui, medicamentos_ui):
    """
    Flujo ESTRICTO:
    1. Generar XML en memoria.
    2. Validar XSD. (Si falla, ABORTAR).
    3. Guardar en BD Local.
    4. Subir a Drive.
    """
    session = SessionLocal()
    try:
        folio_local = f"LOC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # --- PASO 1: GENERAR ESTRUCTURA XML EN MEMORIA ---
        root = ET.Element('receta')
        ET.SubElement(root, 'folio').text = folio_local
        ET.SubElement(root, 'fecha_creacion').text = datetime.now().isoformat()
        
        paciente = ET.SubElement(root, 'paciente')
        ET.SubElement(paciente, 'num_afiliacion').text = datos_ui['num_afiliacion']
        ET.SubElement(paciente, 'nombre_completo').text = datos_ui['paciente_nombre']
        
        doctor = ET.SubElement(root, 'doctor')
        ET.SubElement(doctor, 'cedula').text = datos_ui['doc_cedula']
        ET.SubElement(doctor, 'nombre').text = datos_ui['doc_nombre']
        
        ET.SubElement(root, 'diagnostico').text = datos_ui['diagnostico']
        
        meds_elem = ET.SubElement(root, 'medicamentos')
        for med in medicamentos_ui:
            m = ET.SubElement(meds_elem, 'medicamento')
            ET.SubElement(m, 'nombre').text = med['nombre']
            ET.SubElement(m, 'dosis').text = med['dosis']
            ET.SubElement(m, 'frecuencia').text = med['frecuencia']
            ET.SubElement(m, 'duracion').text = "N/A" 
            ET.SubElement(m, 'notas').text = "Local"

        # --- PASO 2: VALIDACIÓN XSD (EL FILTRO ESTRICTO) ---
        # Aquí es donde decidimos si continuar o cancelar todo
        es_valido, error_xsd = validar_xsd_receta(root)
        
        if not es_valido:
            print(f"⛔ Bloqueado por XSD: {error_xsd}")
            # Retornamos Error inmediatamente. 
            # NO se guarda en BD. NO se sube a Drive.
            return False, f"La receta no cumple con el formato estándar (XSD).\nDetalle: {error_xsd}"
            
        print("✅ XML Validado correctamente. Procediendo a guardar.")

        # --- PASO 3: GUARDAR EN BD (Solo si es válido) ---
        nueva_receta = RecetaLocal(
            folio_web=folio_local,
            num_afiliacion=datos_ui['num_afiliacion'],
            nombre_doctor=datos_ui['doc_nombre'],
            cedula_doctor=datos_ui['doc_cedula'],
            diagnostico=datos_ui['diagnostico'],
            integridad_valida=True,
            impresa=False
        )
        
        for med in medicamentos_ui:
            nueva_receta.medicamentos.append(MedicamentoRecetaLocal(
                nombre_medicamento=med['nombre'],
                dosis=med['dosis'],
                frecuencia=med['frecuencia']
            ))
            
        session.add(nueva_receta)
        session.commit()

        # --- PASO 4: FIRMAR Y SUBIR A DRIVE ---
        # Calculamos el hash seguro
        raw_bytes = ET.tostring(root, encoding='utf-8')
        checksum = calcular_hash_sha256(raw_bytes.decode('utf-8').strip())
        
        metadatos = ET.SubElement(root, 'metadatos')
        ET.SubElement(metadatos, 'origen').text = 'DESKTOP'
        ET.SubElement(metadatos, 'operacion').text = 'ALTA_LOCAL'
        ET.SubElement(metadatos, 'checksum').text = checksum
        
        # Formato bonito para guardar
        xml_final_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")
        
        filename = f"receta_{datos_ui['num_afiliacion']}_{folio_local}.xml"
        service = obtener_servicio()
        
        # Subida directa usando los bytes en memoria
        file_id = subir_archivo_bytes(service, filename, xml_final_str.encode('utf-8'), folder_id=DRIVE_FOLDER_ID_RECETAS)
        
        print(f"☁️ Subido a Drive con ID: {file_id}")
        return True, "Receta creada, validada y sincronizada exitosamente."

    except Exception as e:
        return False, str(e)
    finally:
        session.close()