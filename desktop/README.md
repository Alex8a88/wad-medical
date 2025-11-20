# App Recetas Desktop (Python)

Proyecto de ejemplo que genera recetas médicas en XML, las sube/recupera desde Google Drive y las inserta en una base de datos usando SQLAlchemy (ORM).

## Archivos principales
- config.py: configuración (DB, Drive folder id, credentials file name).
- db.py: modelos SQLAlchemy y funciones de inserción/consulta.
- receta_xml.py: generación y parseo de XML.
- drive_client.py: funciones para usar Google Drive API (requiere `credentials.json`).
- gui.py: interfaz Tkinter con botones "Generar receta" y "Recuperar recetas".
- main.py: arranque de la aplicación.

## Cómo ejecutar
1. Crear y activar un entorno virtual.
2. `pip install -r requirements.txt`.
3. Colocar `credentials.json` (credenciales OAuth de Google) en la carpeta del proyecto y configurar `DRIVE_FOLDER_ID` en `config.py`.
4. Ejecutar `python main.py`.

## Nota
Este repo incluye un archivo SQLite de ejemplo `recetas.db` con datos de muestra para evidencia.
