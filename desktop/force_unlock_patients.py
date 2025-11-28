from db import SessionLocal, PerfilPaciente

def desbloquear_todo():
    print("--- 🔓 Desbloqueando Pacientes ---")
    session = SessionLocal()
    try:
        # Buscar todos los pacientes marcados como inválidos
        pacientes = session.query(PerfilPaciente).all()
        count = 0
        for p in pacientes:
            if not p.integridad_valida:
                p.integridad_valida = True
                count += 1
        
        session.commit()
        print(f"✅ Se desbloquearon {count} pacientes.")
        print("   Ahora puedes generar recetas para ellos.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    desbloquear_todo()