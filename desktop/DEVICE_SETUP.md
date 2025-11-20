# Device Setup Guide

This guide helps you set up the Medical Prescription System desktop application on different devices.

## Issues Fixed

### 1. Google Drive Folder Detection
- **Problem**: Hardcoded folder ID doesn't work on different devices
- **Solution**: Automatic folder detection and configuration

### 2. Patient Loading on First Run
- **Problem**: Incomplete sync function caused crashes
- **Solution**: Robust error handling and complete sync implementation

## Setup Instructions

### First Time Setup on Any Device

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Google Drive Credentials**
   - Go to [Google Cloud Console](https://console.developers.google.com/)
   - Create a project or select existing one
   - Enable Google Drive API
   - Create credentials (OAuth 2.0 Client ID)
   - Download as `credentials.json` and place in the desktop folder

3. **Run Device Setup**
   ```bash
   python setup_device.py
   ```
   
   This will:
   - Verify credentials.json exists
   - Find your "Pacientes" folder in Google Drive
   - Update configuration automatically
   - Test the connection

4. **Start the Application**
   ```bash
   python main.py
   ```

### Manual Configuration (Alternative)

If automatic setup doesn't work:

1. **Find Folder ID Manually**
   ```bash
   python folder_finder.py
   ```

2. **Update .env File**
   Add or update the line:
   ```
   DRIVE_FOLDER_ID=your_folder_id_here
   ```

## Troubleshooting

### "No Pacientes folder found"
- Ensure you have a folder named "Pacientes" in your Google Drive
- Check that your Google account has access to the folder
- Verify credentials.json is correct

### "Authentication failed"
- Delete `token.pickle` and try again
- Verify credentials.json is valid
- Check internet connection

### "Patient sync failed"
- The application will still work without sync
- Check Google Drive permissions
- Verify XML files are in the correct format

### "Database errors"
- Delete `recetas.db` to reset the database
- Run `python init_desktop_db.py` to reinitialize

## File Structure

```
desktop/
├── main.py              # Main application entry
├── setup_device.py      # Device setup script
├── folder_finder.py     # Google Drive folder finder
├── sync_patients.py     # Patient synchronization
├── gui.py              # User interface
├── db.py               # Database models
├── config.py           # Configuration
├── .env                # Environment variables
├── credentials.json    # Google Drive credentials (you provide)
└── requirements.txt    # Python dependencies
```

## Environment Variables

The `.env` file should contain:

```env
# Supabase Configuration (if using)
SUPABASE_URL=your_supabase_url
SUPABASE_API_KEY=your_supabase_key

# Google Drive Configuration
DRIVE_FOLDER_ID=your_folder_id
```

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Verify all dependencies are installed
3. Ensure Google Drive credentials are correct
4. Check that the Pacientes folder exists and is accessible