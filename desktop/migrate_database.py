#!/usr/bin/env python3
"""
Desktop Database Migration Script
Updates the desktop database to match the web application schema
"""

import os
from db import Base, engine, SessionLocal
from init_desktop_db import create_tables, populate_estados, populate_grupos

def backup_existing_database():
    """Create a backup of the existing database"""
    db_path = "recetas.db"
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        print(f"Creating backup: {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
        print("Backup created successfully!")
        return True
    return False

def drop_all_tables():
    """Drop all existing tables"""
    print("Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")

def migrate_database():
    """Main migration function"""
    print("=== Desktop Database Migration ===")
    print("This will update your desktop database to match the web application schema.")
    
    # Ask for confirmation
    response = input("Do you want to proceed? This will backup and recreate your database. (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    try:
        # Step 1: Backup existing database
        backup_created = backup_existing_database()
        if backup_created:
            print("✓ Database backup created")
        
        # Step 2: Drop all tables
        drop_all_tables()
        print("✓ Old tables dropped")
        
        # Step 3: Create new tables
        create_tables()
        print("✓ New tables created")
        
        # Step 4: Populate reference data
        populate_estados()
        print("✓ Mexican states populated")
        
        populate_grupos()
        print("✓ User groups populated")
        
        print("\n🎉 Migration completed successfully!")
        print("Your desktop database now matches the web application schema.")
        
        if backup_created:
            print(f"\nNote: Your old database was backed up as 'recetas.db.backup'")
            print("You can restore it if needed by renaming it back to 'recetas.db'")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Please check the error and try again.")

if __name__ == "__main__":
    migrate_database()