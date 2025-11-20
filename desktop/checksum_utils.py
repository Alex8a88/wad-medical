import hashlib
import xml.etree.ElementTree as ET

def calcular_hash_sha256(texto):
    """Calcula el hash SHA-256 de un string."""
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def limpiar_formato_xml(elemento):
    """
    Elimina espacios en blanco, saltos de línea y sangrías agregados por 'pretty print'.
    Deja el objeto XML como si fuera 'crudo'.
    """
    # Limpiar texto del elemento (ej. espacios alrededor de "Juan")
    if elemento.text:
        elemento.text = elemento.text.strip()
    
    # Limpiar 'tail' (espacios después de la etiqueta de cierre </tag> espacio <tag>)
    if elemento.tail:
        elemento.tail = elemento.tail.strip()
    
    # Recursividad para hijos
    for hijo in elemento:
        limpiar_formato_xml(hijo)

def verificar_checksum_xml(ruta_archivo):
    """
    Reconstruye el estado original del XML (sin metadatos y sin formato)
    para verificar el checksum exactamente como lo calculó el backend.
    """
    print(f"🔍 Validando (Reconstrucción de Objeto): {ruta_archivo}")
    
    try:
        # 1. Parsear el archivo XML usando la librería oficial
        # Esto maneja automáticamente BOM y encodings
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        
        # 2. Extraer Checksum Declarado de <metadatos>
        metadatos = root.find('metadatos')
        if metadatos is None:
            return False, "XML sin bloque de metadatos"
            
        checksum_elem = metadatos.find('checksum')
        if checksum_elem is None or not checksum_elem.text:
            return False, "Etiqueta checksum vacía o faltante"
            
        checksum_declarado = checksum_elem.text.strip().lower()
        
        # 3. RECONSTRUCCIÓN DEL ESTADO ORIGINAL
        # El backend calculó el hash sobre el root SIN metadatos
        root.remove(metadatos)
        
        # 4. LIMPIEZA DE FORMATO (CRÍTICO)
        # El archivo en disco tiene "pretty print" (espacios/enters de minidom).
        # El backend calculó el hash sobre la versión "compacta".
        # Debemos quitarle todo el maquillaje para que coincida.
        limpiar_formato_xml(root)
        
        # 5. Generar String para Hash
        # Usamos exactamente la misma lógica que tu backend:
        # core_xml_bytes = ET.tostring(root, encoding='utf-8')
        # core_xml_string_for_hash = core_xml_bytes.decode('utf-8').strip()
        
        raw_bytes = ET.tostring(root, encoding='utf-8')
        contenido_a_hashear = raw_bytes.decode('utf-8').strip()
        
        # 6. Calcular Hash
        checksum_calculado = calcular_hash_sha256(contenido_a_hashear)
        
        # 7. Comparar
        if checksum_calculado == checksum_declarado:
            return True, "Checksum válido"
        else:
            # Debug para que veas si falla
            print(f"   ❌ Fallo - Esperado: {checksum_declarado}")
            print(f"   ❌ Fallo - Calculado: {checksum_calculado}")
            return False, "Contenido alterado"
            
    except Exception as e:
        print(f"Error procesando XML: {e}")
        return False, f"Error: {e}"