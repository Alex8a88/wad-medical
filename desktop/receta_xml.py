# receta_xml.py - generate and parse XML for recetas
import xml.etree.ElementTree as ET

def generar_xml_receta(receta_dict):
    root = ET.Element('receta')
    
    # Add receta ID if available
    if 'id' in receta_dict:
        ET.SubElement(root, 'id').text = str(receta_dict['id'])

    paciente = ET.SubElement(root, 'paciente')
    ET.SubElement(paciente, 'nombre').text = receta_dict['paciente']['nombre']
    ET.SubElement(paciente, 'edad').text = str(receta_dict['paciente'].get('edad',''))
    ET.SubElement(paciente, 'genero').text = receta_dict['paciente'].get('genero','')
    ET.SubElement(paciente, 'correo').text = receta_dict['paciente'].get('correo','').lower()

    medico = ET.SubElement(root, 'medico')
    ET.SubElement(medico, 'nombre').text = receta_dict['medico']['nombre']
    ET.SubElement(medico, 'cedula').text = receta_dict['medico'].get('cedula','')

    ET.SubElement(root, 'diagnostico').text = receta_dict.get('diagnostico','')

    meds = ET.SubElement(root, 'medicamentos')
    for m in receta_dict.get('medicamentos', []):
        med = ET.SubElement(meds, 'medicamento')
        ET.SubElement(med, 'nombre').text = m.get('nombre')
        ET.SubElement(med, 'dosis').text = m.get('dosis')
        ET.SubElement(med, 'frecuencia').text = m.get('frecuencia')

    xml_bytes = ET.tostring(root, encoding='utf-8', method='xml')
    return xml_bytes

def parsear_xml_a_dict(xml_bytes_or_str):
    if isinstance(xml_bytes_or_str, bytes):
        root = ET.fromstring(xml_bytes_or_str)
    else:
        root = ET.fromstring(xml_bytes_or_str.encode('utf-8'))

    receta = {}
    
    # Parse receta ID if present
    id_element = root.find('id')
    if id_element is not None and id_element.text:
        receta['id'] = int(id_element.text)
        
    paciente = root.find('paciente')
    if paciente is not None:
        receta['paciente'] = {
            'nombre': paciente.findtext('nombre',''),
            'edad': int(paciente.findtext('edad','0')) if paciente.findtext('edad') else None,
            'genero': paciente.findtext('genero',''),
            'correo': paciente.findtext('correo','').lower()
        }
    
    medico = root.find('medico')
    if medico is not None:
        receta['medico'] = {
            'nombre': medico.findtext('nombre',''),
            'cedula': medico.findtext('cedula','')
        }
    receta['diagnostico'] = root.findtext('diagnostico','')
    receta['medicamentos'] = []
    for m in root.findall('./medicamentos/medicamento'):
        receta['medicamentos'].append({
            'nombre': m.findtext('nombre',''),
            'dosis': m.findtext('dosis',''),
            'frecuencia': m.findtext('frecuencia','')
        })

    return receta
