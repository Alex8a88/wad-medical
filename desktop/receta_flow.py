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
    try:
        xsd_path = os.path.join(os.path.dirname(__file__), 'schemas', 'receta.xsd')
        schema_doc = etree.parse(xsd_path)
        schema = etree.XMLSchema(schema_doc)
        xml_str = ET.tostring(xml_root)
        doc = etree.fromstring(xml_str)
        schema.assertValid(doc)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def procesar_nueva_receta_local(datos_ui, medicamentos_ui):
    session = SessionLocal()
    try:
        # 1. Guardar Local
        folio_local = f"LOC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
        print(f"✅ Receta guardada localmente: {folio_local}")

        # 2. Generar XML
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
            ET.SubElement(m, 'notas').text = "Generada localmente"

        # 3. VALIDAR XSD
        es_valido, error_xsd = validar_xsd_receta(root)
        if not es_valido:
            raise ValueError(f"Estructura XML inválida según XSD: {error_xsd}")
        print("✅ Estructura XSD válida.")

        # 4. Checksum y Subida
        raw_bytes = ET.tostring(root, encoding='utf-8')
        checksum = calcular_hash_sha256(raw_bytes.decode('utf-8').strip())
        
        metadatos = ET.SubElement(root, 'metadatos')
        ET.SubElement(metadatos, 'origen').text = 'DESKTOP_APP'
        ET.SubElement(metadatos, 'operacion').text = 'ALTA_LOCAL'
        ET.SubElement(metadatos, 'checksum').text = checksum
        
        xml_final_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")
        
        filename = f"receta_{datos_ui['num_afiliacion']}_{folio_local}.xml"
        service = obtener_servicio()
        
        # Guardar temporalmente para subir (si tu función subir_archivo requiere path)
        # O ajustar subir_archivo_bytes para recibir contenido directo
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_final_str)
            
        file_id = subir_archivo_bytes(service, filename, xml_final_str.encode('utf-8'), folder_id=DRIVE_FOLDER_ID_RECETAS)
        
        if os.path.exists(filename): os.remove(filename)
        print(f"☁️ Subido a Drive con ID: {file_id}")

        return True, "Receta creada, validada y subida exitosamente."

    except Exception as e:
        return False, str(e)
    finally:
        session.close()