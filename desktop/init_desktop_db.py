#!/usr/bin/env python3
"""
Desktop Database Initialization Script
Creates the desktop database with the same structure as the backend
"""

from db import Base, engine, SessionLocal, CatalogoEstados, Grupos
from sqlalchemy import text

def create_tables():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

def populate_estados():
    """Populate Mexican states"""
    session = SessionLocal()
    try:
        # Check if estados already exist
        if session.query(CatalogoEstados).count() > 0:
            print("Estados already populated, skipping...")
            return
        
        estados_mexicanos = [
            'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche',
            'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima',
            'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo',
            'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca',
            'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa',
            'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'
        ]
        
        print("Populating Mexican states...")
        for estado in estados_mexicanos:
            estado_obj = CatalogoEstados(nombre_estado=estado)
            session.add(estado_obj)
        
        session.commit()
        print(f"Successfully added {len(estados_mexicanos)} states!")
        
    except Exception as e:
        session.rollback()
        print(f"Error populating estados: {e}")
    finally:
        session.close()

def populate_grupos():
    """Populate user groups"""
    session = SessionLocal()
    try:
        # Check if grupos already exist
        if session.query(Grupos).count() > 0:
            print("Grupos already populated, skipping...")
            return
        
        grupos = ['Administrador', 'Doctor', 'Paciente', 'Mesa de Ayuda']
        
        print("Populating user groups...")
        for grupo in grupos:
            grupo_obj = Grupos(nombre_grupo=grupo)
            session.add(grupo_obj)
        
        session.commit()
        print(f"Successfully added {len(grupos)} groups!")
        
    except Exception as e:
        session.rollback()
        print(f"Error populating grupos: {e}")
    finally:
        session.close()

def main():
    """Main initialization function"""
    print("Initializing desktop database...")
    
    try:
        create_tables()
        populate_estados()
        populate_grupos()
        print("\nDesktop database initialization completed successfully!")
        
    except Exception as e:
        print(f"Error during initialization: {e}")

if __name__ == "__main__":
    main()