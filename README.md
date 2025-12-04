Sistema Médico de Gestión de Recetas (WAD) 🏥💊

Este proyecto es una solución híbrida (Web + Escritorio) diseñada para la gestión segura, emisión y sincronización de recetas médicas en consultorios distribuidos.

🚀 Características Principales

🌐 Aplicación Web (Backend - Django REST Framework)

Gestión Centralizada: Administración de pacientes, doctores y catálogo de medicamentos.

Generación de Recetas: Creación de recetas digitales con exportación automática a PDF.

Seguridad Avanzada: Validación estricta de estructura XML mediante esquemas XSD antes de cualquier operación.

Integración en la Nube: Sube automáticamente las recetas generadas a Google Drive organizadas por carpetas.

Notificaciones: Envío automático de la receta y contraseña de seguridad por correo electrónico al paciente.

🖥️ Aplicación de Escritorio (Cliente Local - Tkinter)

Modo Offline: Base de datos local (SQLite) que permite consultar historiales sin internet.

Sincronización Inteligente: Descarga recetas nuevas desde Google Drive.

Verificación de Integridad: Sistema robusto de Checksum (SHA-256) que detecta si un archivo XML fue alterado externamente o corrompido (diferenciando formatos Windows/Linux).

Impresión Directa: Módulo de impresión nativa para mandar la receta a la impresora física del consultorio con un solo clic.

Generación Local: Capacidad de crear recetas localmente, validarlas contra XSD y subirlas a la nube.

🛠️ Tecnologías Utilizadas

Backend: Python, Django, Django REST Framework.

Frontend: React (Panel de administración web).

Escritorio: Python, Tkinter, ReportLab (PDF), Win32print.

Servicios Cloud: Google Drive API v3, Gmail SMTP.

Seguridad: Hashing SHA-256, Validación XSD (lxml).

🔄 Flujo de Datos

Creación: El médico genera la receta en la Web o en Local.

Validación: El sistema valida la estructura (XSD) y firma los datos (Checksum).

Transporte: El archivo XML seguro se sube a Google Drive.

Sincronización: La app de escritorio descarga el XML, verifica que la firma coincida y lo guarda en la BD local.

Salida: La receta se imprime físicamente y/o se envía por correo al paciente.
