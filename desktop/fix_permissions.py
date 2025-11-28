import os

def fix_permissions():
    print("--- 🔄 Reparación de Permisos de Drive ---")
    
    # Este es el archivo que guarda tu sesión iniciada.
    # Actualmente tiene guardado que solo puedes LEER.
    # Necesitamos borrarlo para iniciar sesión de nuevo y poder ESCRIBIR.
    token_file = 'token.pickle'
    
    if os.path.exists(token_file):
        try:
            os.remove(token_file)
            print(f"✅ Archivo eliminado exitosamente: {token_file}")
            print("---------------------------------------------------")
            print("   AHORA SIGUE ESTOS PASOS:")
            print("   1. Abre tu aplicación 'App Recetas' nuevamente.")
            print("   2. Se abrirá una ventana en tu navegador de internet.")
            print("   3. Inicia sesión con tu cuenta de Google.")
            print("   4. IMPORTANTE: Dale clic a 'Continuar' o 'Permitir' en todas las pantallas.")
            print("---------------------------------------------------")
        except Exception as e:
            print(f"❌ Error al intentar borrar el archivo: {e}")
            print("   Intenta borrarlo manualmente yendo a la carpeta 'desktop'.")
    else:
        print(f"ℹ️ No se encontró el archivo {token_file}.")
        print("   Esto es bueno. Significa que ya puedes abrir tu App para iniciar sesión con los nuevos permisos.")

if __name__ == "__main__":
    fix_permissions()