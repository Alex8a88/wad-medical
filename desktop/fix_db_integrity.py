import sqlite3
import os

# Nombre de tu base de datos (basado en tu main.py)
DB_NAME = 'recetas.db'

def repair_database():
    print(f"Verificando base de datos: {DB_NAME}...")
    
    if not os.path.exists(DB_NAME):
        print(f"❌ Error: No se encontró el archivo {DB_NAME} en esta carpeta.")
        print("Asegúrate de ejecutar este script en la misma carpeta donde está main.py")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # 1. Verificar columnas en tabla 'perfil_paciente'
        print("Inspeccionando tabla 'perfil_paciente'...")
        cursor.execute("PRAGMA table_info(perfil_paciente)")
        columns_info = cursor.fetchall()
        
        # Extraer nombres de las columnas
        column_names = [info[1] for info in columns_info]
        
        # 2. Agregar columna si falta
        if 'integridad_valida' not in column_names:
            print("⚠️ Falta la columna 'integridad_valida'. Agregándola...")
            
            # Agregamos la columna como BOOLEAN (que en SQLite es INTEGER 0 o 1)
            # Default 1 (True) para asumir que los existentes son válidos
            cursor.execute("ALTER TABLE perfil_paciente ADD COLUMN integridad_valida BOOLEAN DEFAULT 1")
            conn.commit()
            print("✅ Columna 'integridad_valida' agregada exitosamente.")
        else:
            print("✅ La columna 'integridad_valida' ya existe. No es necesario hacer cambios.")

    except Exception as e:
        print(f"❌ Ocurrió un error al modificar la base de datos: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("Operación finalizada.")

if __name__ == "__main__":
    repair_database()