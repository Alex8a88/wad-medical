import os
import time
import platform

def enviar_a_impresora(ruta_archivo):
    """
    Manda el archivo a la cola de impresión de Windows.
    Si falla la impresión automática, abre el archivo para impresión manual.
    """
    try:
        # 1. Asegurar ruta absoluta
        ruta_abs = os.path.abspath(ruta_archivo)
        
        if not os.path.exists(ruta_abs):
            return False, f"El archivo no existe: {ruta_archivo}"

        print(f"🖨️ Procesando archivo: {ruta_abs}")

        if platform.system() == "Windows":
            try:
                # INTENTO A: Impresión Directa (Ideal)
                # Funciona si tienes Adobe Reader u otro visor completo instalado.
                os.startfile(ruta_abs, "print")
                
                # Damos tiempo al sistema para registrar el comando
                time.sleep(2) 
                return True, "Enviado a la impresora correctamente."
            
            except OSError:
                # INTENTO B: Fallback (Plan de Respaldo)
                # Si Windows da error 1155 (No hay asociación para imprimir),
                # abrimos el archivo normalmente para que el usuario lo imprima.
                print("⚠️ Advertencia: Windows no soporta impresión automática en este equipo.")
                try:
                    os.startfile(ruta_abs) # Esto equivale a doble clic
                    return True, "Abierto para impresión manual (Falta configurar Adobe Reader para automático)."
                except Exception as e2:
                    return False, f"Error: No se pudo abrir el archivo. {e2}"
        else:
            return False, "Solo soportado en Windows."

    except Exception as e:
        return False, f"Error crítico al intentar imprimir: {e}"