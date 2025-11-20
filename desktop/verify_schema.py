#!/usr/bin/env python3
"""
Desktop Database Schema Verification Script
Checks if the desktop database schema matches the web application
"""

from db import engine, SessionLocal, Usuario, PerfilPaciente, Direcciones, CatalogoEstados, Grupos
from sqlalchemy import inspect

def verify_schema():
    """Verify database schema and data"""
    print("=== Desktop Database Schema Verification ===")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            'usuarios', 'perfil_paciente', 'direcciones', 
            'catalogo_estados', 'grupos', 'medicos', 
            'recetas', 'medicamentos', 'receta_medicamentos'
        ]
        
        print("Checking tables...")
        missing_tables = []
        for table in expected_tables:
            if table in tables:
                print(f"✓ {table}")
            else:
                print(f"❌ {table} - MISSING")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n⚠️  Missing tables: {missing_tables}")
            print("Run 'python migrate_database.py' to fix this.")
            return False
        
        # Check reference data
        session = SessionLocal()
        try:
            estados_count = session.query(CatalogoEstados).count()
            grupos_count = session.query(Grupos).count()
            
            print(f"\nReference data:")
            print(f"✓ Estados: {estados_count} records")
            print(f"✓ Grupos: {grupos_count} records")
            
            if estados_count == 0 or grupos_count == 0:
                print("⚠️  Missing reference data. Run 'python init_desktop_db.py' to populate.")
        
        finally:
            session.close()
        
        print("\n🎉 Database schema verification completed!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    verify_schema()