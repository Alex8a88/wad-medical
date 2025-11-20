#!/usr/bin/env python3
"""
Device Setup Script
Configures the application for use on different devices
"""

import os
import sys
from folder_finder import find_pacientes_folder, update_env_file

def setup_device():
    """Setup the application for this device"""
    print("=== Medical Prescription System - Device Setup ===")
    print()
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("Please download your Google Drive API credentials and save as 'credentials.json'")
        print("Get credentials from: https://console.developers.google.com/")
        return False
    
    print("✓ Found credentials.json")
    
    # Find and configure Google Drive folder
    print("\nSearching for 'Pacientes' folder in Google Drive...")
    folder_id = find_pacientes_folder()
    
    if not folder_id:
        print("❌ Could not find or configure Pacientes folder")
        return False
    
    # Update .env file
    update_env_file(folder_id)
    
    # Test the configuration
    print("\nTesting configuration...")
    try:
        from sync_patients import authenticate_google_drive, fetch_patient_files
        service = authenticate_google_drive()
        files = fetch_patient_files(service, folder_id)
        print(f"✓ Successfully connected to Google Drive")
        print(f"✓ Found {len(files)} patient files in the folder")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    print("\n🎉 Device setup completed successfully!")
    print("You can now run the application with: python main.py")
    return True

if __name__ == '__main__':
    success = setup_device()
    if not success:
        sys.exit(1)