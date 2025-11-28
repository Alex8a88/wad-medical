import hashlib
import xml.etree.ElementTree as ET

def calcular_hash_sha256(texto):
    """Calcula el hash SHA-256 de un string."""
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def limpiar_formato_xml(elemento):
    """
    Elimina espacios en blanco, saltos de línea y sangrías de forma recursiva.
    Deja el objeto XML en su estado 'crudo' original.
    """
    # Limpiar texto del elemento (ej. espacios alrededor de "Juan")
    if elemento.text:
        elemento.text = elemento.text.strip()
    
    # Limpiar 'tail' (espacios después de la etiqueta de cierre)
    if elemento.tail:
        elemento.tail = elemento.tail.strip()
    
    # Recursividad para limpiar a los hijos
    for hijo in elemento:
        limpiar_formato_xml(hijo)

def verificar_checksum_xml(ruta_archivo):
    """
    Verifica la integridad reconstruyendo el objeto XML original.
    Funciona para PACIENTES y RECETAS por igual.
    """
    print(f"🔍 Validando integridad: {ruta_archivo}")
    
    try:
        # 1. Parsear el archivo (Maneja BOM y encodings automáticamente)
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        
        # 2. Buscar el checksum declarado
        metadatos = root.find('metadatos')
        if metadatos is None:
            print("   ❌ Error: XML sin metadatos.")
            return False, "Sin metadatos"
            
        checksum_elem = metadatos.find('checksum')
        if checksum_elem is None or not checksum_elem.text:
            print("   ❌ Error: Metadatos sin checksum.")
            return False, "Sin checksum"
            
        checksum_declarado = checksum_elem.text.strip().lower()
        
        # 3. RECONSTRUCCIÓN (La clave del éxito)
        # Quitamos los metadatos del objeto en memoria
        root.remove(metadatos)
        
        # Quitamos todo el formato bonito (pretty print)
        limpiar_formato_xml(root)
        
        # 4. Generar el string crudo (igual que en el backend)
        raw_bytes = ET.tostring(root, encoding='utf-8')
        # Decodificamos y hacemos strip por si queda algún caracter invisible
        contenido_a_hashear = raw_bytes.decode('utf-8').strip()
        
        # 5. Calcular Hash
        checksum_calculado = calcular_hash_sha256(contenido_a_hashear)
        
        # 6. Comparar
        if checksum_calculado == checksum_declarado:
            print("   ✅ Integridad CORRECTA.")
            return True, "Válido"
        else:
            print(f"   ❌ FALLO: Calculado {checksum_calculado[:8]}... != Declarado {checksum_declarado[:8]}...")
            return False, "Alterado"
            
    except Exception as e:
        print(f"   ⚠️ Excepción validando: {e}")
        return False, str(e)