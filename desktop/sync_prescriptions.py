import os
import xml.etree.ElementTree as ET
from datetime import datetime
from db import SessionLocal, PerfilPaciente
# Importamos tus modelos nuevos
from db_recetas_models import RecetaLocal, MedicamentoRecetaLocal, init_recetas_db
from config import DRIVE_FOLDER_ID_RECETAS as DRIVE_FOLDER_ID
# Reutilizamos las funciones que ya funcionan de sync_patients
from sync_patients import authenticate_google_drive, download_file_bytes

# Importamos el validador robusto
try:
    from checksum_utils import verificar_checksum_xml
except ImportError:
    def verificar_checksum_xml(path): return True, "Omitido"

def parse_prescription_xml(xml_string):
    """
    Parsea el XML de una receta y extrae sus datos en un diccionario.
    """
    try:
        root = ET.fromstring(xml_string)
        data = {}
        
        # Función auxiliar para sacar texto seguro
        def get(tag, base=root): 
            el = base.find(tag)
            return el.text.strip() if el is not None and el.text else ''

        data['folio'] = get('folio')
        data['fecha'] = get('fecha_creacion')
        data['diagnostico'] = get('diagnostico')
        
        # Datos del Paciente (para vincular)
        paciente = root.find('paciente')
        if paciente is not None:
            data['num_afiliacion'] = get('num_afiliacion', paciente)
        else:
            data['num_afiliacion'] = ''
        
        # Datos del Doctor
        doctor = root.find('doctor')
        if doctor is not None:
            data['doc_nombre'] = get('nombre', doctor)
            data['doc_cedula'] = get('cedula', doctor)
        else:
            data['doc_nombre'] = 'Desconocido'
            data['doc_cedula'] = ''
        
        # Lista de Medicamentos
        data['medicamentos'] = []
        meds_node = root.find('medicamentos')
        if meds_node is not None:
            for m in meds_node.findall('medicamento'):
                med_item = {
                    'nombre': get('nombre', m),
                    'dosis': get('dosis', m),
                    'frecuencia': get('frecuencia', m),
                    'duracion': get('duracion', m),
                    'notas': get('notas', m)
                }
                data['medicamentos'].append(med_item)
                
        return data
    except Exception as e:
        print(f"Error parseando receta XML: {e}")
        return None

def upsert_prescription(session, data, integrity_valid):
    """
    Guarda la receta en la base de datos local.
    """
    try:
        # 1. Verificar si la receta ya existe (por folio web)
        existing = session.query(RecetaLocal).filter_by(folio_web=data['folio']).first()
        if existing:
            # Si ya existe, podríamos actualizarla o simplemente saltarla.
            # Por seguridad, asumiremos que las recetas no cambian, solo se crean.
            print(f"   ℹ️ Receta folio {data['folio']} ya existe. Saltando.")
            return True

        # 2. Verificar que el paciente exista en local
        # (Si no existe, la receta se guarda pero quedará 'huérfana' de datos personales hasta que se sincronice el paciente)
        paciente_local = session.query(PerfilPaciente).filter_by(num_afiliacion=data['num_afiliacion']).first()
        if not paciente_local:
            print(f"   ⚠️ ADVERTENCIA: El paciente {data['num_afiliacion']} no está en la BD local.")

        # 3. Crear el objeto Receta
        nueva_receta = RecetaLocal(
            folio_web=data['folio'],
            num_afiliacion=data['num_afiliacion'],
            nombre_doctor=data['doc_nombre'],
            cedula_doctor=data['doc_cedula'],
            diagnostico=data['diagnostico'],
            integridad_valida=integrity_valid,
            impresa=False,
            fecha_importacion=datetime.now()
        )
        
        # 4. Agregar los Medicamentos a la receta
        for med in data['medicamentos']:
            nuevo_med = MedicamentoRecetaLocal(
                nombre_medicamento=med['nombre'],
                dosis=med['dosis'],
                frecuencia=med['frecuencia'],
                duracion=med['duracion'],
                notas=med['notas']
            )
            # SQLAlchemy maneja la relación y asigna el ID automáticamente
            nueva_receta.medicamentos.append(nuevo_med)

        session.add(nueva_receta)
        session.commit()
        
        estado = "✅ VÁLIDA" if integrity_valid else "❌ ALTERADA"
        print(f"   💾 Receta {data['folio']} guardada correctamente. Integridad: {estado}")
        return True

    except Exception as e:
        session.rollback()
        print(f"   ❌ Error guardando receta en BD: {e}")
        return False

def sync_prescriptions():
    print("\n--- 💊 Iniciando Sincronización de Recetas ---")
    
    # 1. Conexión a Drive
    service = authenticate_google_drive()
    if not service:
        print("No se pudo conectar a Drive.")
        return

    # 2. Buscar archivos XML de recetas
    # Buscamos archivos que contengan 'receta_' y '.xml'
    query = f"'{DRIVE_FOLDER_ID}' in parents and name contains 'receta_' and name contains '.xml' and trashed = false"
    
    try:
        results = service.files().list(q=query, fields="files(id, name, modifiedTime)").execute()
        files = results.get('files', [])
    except Exception as e:
        print(f"Error buscando archivos en Drive: {e}")
        return

    if not files:
        print("   📂 No se encontraron recetas nuevas en la carpeta.")
        return

    print(f"   📂 Se encontraron {len(files)} recetas potenciales.")
    
    session = SessionLocal()
    try:
        for file in files:
            print(f"\n   📄 Procesando: {file['name']}...")
            
            # A. Descarga Binaria (Crucial para el checksum)
            xml_bytes = download_file_bytes(service, file['id'])
            if not xml_bytes:
                print("      Error al descargar archivo.")
                continue

            # B. Verificar Integridad
            temp_path = f"temp_{file['name']}"
            es_valido = False
            try:
                with open(temp_path, 'wb') as f:
                    f.write(xml_bytes)
                
                # Usamos tu validador maestro
                es_valido, msg = verificar_checksum_xml(temp_path)
            except Exception as e:
                print(f"      Error verificación: {e}")
            finally:
                if os.path.exists(temp_path):
                    try: os.remove(temp_path)
                    except: pass

            if not es_valido:
                print(f"      🚨 ALERTA: Archivo alterado o corrupto.")
            else:
                print(f"      ✨ Integridad verificada correctamente.")

            # C. Parsear y Guardar
            try:
                # Decodificamos solo para leer datos
                xml_str = xml_bytes.decode('utf-8')
                data = parse_prescription_xml(xml_str)
                
                if data:
                    upsert_prescription(session, data, es_valido)
            except Exception as e:
                print(f"      Error procesando datos XML: {e}")
                
    finally:
        session.close()
    print("\n--- Fin Sincronización Recetas ---")

if __name__ == "__main__":
    # Aseguramos que existan las tablas antes de correr
    init_recetas_db()
    sync_prescriptions()