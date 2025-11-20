import hashlib

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