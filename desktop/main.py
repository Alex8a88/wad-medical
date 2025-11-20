# main.py
import os
from gui import AppRecetas
from db import init_db
from sync_patients import sync_patients_from_drive
from migrate_email_tracking import migrate_add_envios_email

def first_time_setup():
    """Check if this is first run and perform setup"""
    db_exists = os.path.exists('recetas.db')
    
    if not db_exists:
        print("First time setup detected...")
        
        # Initialize database
        print("Initializing database...")
        init_db()
        
        # Add email tracking table
        print("Setting up email tracking...")
        migrate_add_envios_email()
        
        # Ask user if they want to sync patients
        response = input("Do you want to sync patient data from Google Drive? (y/N): ")
        if response.lower() == 'y':
            try:
                sync_patients_from_drive()
            except Exception as e:
                print(f"Error during initial sync: {e}")
                print("You can try syncing later from the application.")
        
        print("Setup completed!")
    else:
        # For existing databases, ensure email tracking table exists
        migrate_add_envios_email()
    
    return db_exists

if __name__ == '__main__':
    # Perform first-time setup if needed
    first_time_setup()
    
    # Sync patients from Google Drive on every start
    print("Syncing patients from Google Drive...")
    try:
        sync_success = sync_patients_from_drive()
        if not sync_success:
            print("Warning: Patient sync had issues. Check your Google Drive connection.")
    except Exception as e:
        print(f"Warning: Could not sync patients from Google Drive: {e}")
        print("The application will continue without patient sync.")
    
    # Start the application
    app = AppRecetas()
    app.mainloop()