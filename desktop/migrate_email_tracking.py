#!/usr/bin/env python3
"""
Database Migration: Add envios_email table
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_envios_email():
    """Add envios_email table to existing database"""
    db_path = 'recetas.db'
    
    if not os.path.exists(db_path):
        print("Database file not found. Run the application first to create it.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='envios_email'")
        if cursor.fetchone():
            print("envios_email table already exists")
            conn.close()
            return True
        
        # Create envios_email table
        cursor.execute('''
            CREATE TABLE envios_email (
                id INTEGER PRIMARY KEY,
                receta_id INTEGER NOT NULL,
                destinatario VARCHAR(250) NOT NULL,
                tipo_email VARCHAR(20) NOT NULL,
                asunto VARCHAR(500) NOT NULL,
                estado VARCHAR(20) NOT NULL,
                mensaje_error TEXT,
                fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (receta_id) REFERENCES recetas (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✓ envios_email table created successfully")
        return True
        
    except Exception as e:
        print(f"Error creating envios_email table: {e}")
        return False

if __name__ == "__main__":
    migrate_add_envios_email()