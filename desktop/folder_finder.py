#!/usr/bin/env python3
"""
Google Drive Folder Finder
Automatically finds the Pacientes folder on different devices
"""

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_google_drive():
    """Authenticate with Google Drive API"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def find_pacientes_folder():
    """Find the Pacientes folder in Google Drive"""
    try:
        service = authenticate_google_drive()
        
        # Search for folders named "Pacientes"
        results = service.files().list(
            q="name='Pacientes' and mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name, parents)"
        ).execute()
        
        folders = results.get('files', [])
        
        if not folders:
            print("No 'Pacientes' folder found in Google Drive")
            return None
        
        if len(folders) == 1:
            folder_id = folders[0]['id']
            print(f"Found Pacientes folder: {folder_id}")
            return folder_id
        
        # Multiple folders found, let user choose
        print("Multiple 'Pacientes' folders found:")
        for i, folder in enumerate(folders):
            print(f"{i+1}. {folder['name']} (ID: {folder['id']})")
        
        while True:
            try:
                choice = int(input("Select folder (enter number): ")) - 1
                if 0 <= choice < len(folders):
                    return folders[choice]['id']
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
                
    except Exception as e:
        print(f"Error finding Pacientes folder: {e}")
        return None

def update_env_file(folder_id):
    """Update .env file with the found folder ID"""
    env_path = '.env'
    
    # Read existing .env content
    env_content = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.readlines()
    
    # Update or add DRIVE_FOLDER_ID
    updated = False
    for i, line in enumerate(env_content):
        if line.startswith('DRIVE_FOLDER_ID='):
            env_content[i] = f'DRIVE_FOLDER_ID={folder_id}\n'
            updated = True
            break
    
    if not updated:
        env_content.append(f'DRIVE_FOLDER_ID={folder_id}\n')
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(env_content)
    
    print(f"Updated .env file with DRIVE_FOLDER_ID={folder_id}")

if __name__ == '__main__':
    folder_id = find_pacientes_folder()
    if folder_id:
        update_env_file(folder_id)
        print("Setup complete! The application will now use the correct Pacientes folder.")
    else:
        print("Could not find or select Pacientes folder. Please check your Google Drive setup.")