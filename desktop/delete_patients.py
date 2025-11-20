import sqlite3
import os

DB_NAME = 'recetas.db'

def connect_db():
    if not os.path.exists(DB_NAME):
        print(f"❌ No se encontró la base de datos '{DB_NAME}'.")
        return None
    return sqlite3.connect(DB_NAME)

def delete_all_patients():
    """Elimina TODOS los pacientes, usuarios y direcciones."""
    conn = connect_db()
    if not conn: return

    cursor = conn.cursor()
    try:
        print("⚠️  ADVERTENCIA: Esto borrará TODOS los pacientes de la base de datos local.")
        confirm = input("¿Estás seguro? Escribe 'SI' para confirmar: ")
        
        if confirm != 'SI':
            print("Operación cancelada.")
            return

        # Borrar datos en orden para evitar problemas de integridad referencial
        print("Borrando perfiles de pacientes...")
        cursor.execute("DELETE FROM perfil_paciente")
        
        print("Borrando direcciones...")
        cursor.execute("DELETE FROM direcciones")
        
        print("Borrando usuarios...")
        cursor.execute("DELETE FROM usuarios")
        
        # Opcional: Reiniciar contadores de ID
        # Usamos try-except por si la tabla sqlite_sequence no existe (pasa en DBs nuevas)
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='usuarios'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='perfil_paciente'")
        except sqlite3.OperationalError:
            # Si la tabla no existe, simplemente ignoramos este paso
            pass
        
        conn.commit()
        print(f"✅ Base de datos '{DB_NAME}' limpiada exitosamente.")
        print("Ahora puedes correr main.py para volver a sincronizar desde Drive.")
        
    except Exception as e:
        print(f"❌ Error al eliminar: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_single_patient():
    """Elimina un paciente específico por Num. Afiliación."""
    conn = connect_db()
    if not conn: return

    cursor = conn.cursor()
    num_afiliacion = input("Ingresa el Número de Afiliación del paciente a eliminar: ").strip()
    
    try:
        # 1. Buscar el ID de usuario asociado a ese paciente
        cursor.execute("SELECT id_usuario, id_paciente FROM perfil_paciente WHERE num_afiliacion = ?", (num_afiliacion,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ No se encontró ningún paciente con afiliación '{num_afiliacion}'.")
            return

        id_usuario, id_paciente = result
        print(f"Encontrado: Paciente ID {id_paciente} asociado al Usuario ID {id_usuario}")
        
        # 2. Eliminar
        # Borramos perfil
        cursor.execute("DELETE FROM perfil_paciente WHERE id_paciente = ?", (id_paciente,))
        # Borramos dirección
        cursor.execute("DELETE FROM direcciones WHERE id_usuario = ?", (id_usuario,))
        # Borramos usuario (padre)
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = ?", (id_usuario,))
        
        conn.commit()
        print(f"✅ Paciente con afiliación '{num_afiliacion}' eliminado correctamente.")
        
    except Exception as e:
        print(f"❌ Error al eliminar: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    print("--- GESTIÓN DE ELIMINACIÓN DE PACIENTES ---")
    print("1. Eliminar UN paciente específico")
    print("2. Eliminar TODOS los pacientes (Limpieza total)")
    print("3. Salir")
    
    choice = input("\nSelecciona una opción (1-3): ")
    
    if choice == '1':
        delete_single_patient()
    elif choice == '2':
        delete_all_patients()
    else:
        print("Saliendo...")

if __name__ == "__main__":
    main()