from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import models
from .models import PerfilPaciente
from .serializers import PatientRegistrationSerializer, PatientUpdateSerializer
from users.models import Usuario
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from django.conf import settings
from .utils import calcular_hash_sha256
from xml.dom import minidom # Se agregó esta importación para el formateo
# No se requiere el 'import base64'

def create_patient_xml(perfil_paciente):
    """
    Crea el archivo XML para la sincronización y lo guarda en la carpeta xml_files.
    Llama a create_patient_xml_content para obtener el string con el checksum.
    """
    # Obtenemos el contenido XML (que ya incluye el checksum)
    xml_final_content = create_patient_xml_content(perfil_paciente)
    
    # Lógica original para el nombre y guardado del archivo
    usuario = perfil_paciente.id_usuario
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    primer_nombre = usuario.primer_nombre.replace(' ', '') if usuario.primer_nombre else 'Unknown'
    primer_apellido = usuario.primer_apellido.replace(' ', '') if usuario.primer_apellido else 'Unknown'
    filename = f"paciente_{primer_nombre}_{primer_apellido}_{timestamp}.xml"
    
    # Save to XML folder
    xml_folder = os.path.join(settings.BASE_DIR, 'xml_files')
    os.makedirs(xml_folder, exist_ok=True)
    filepath = os.path.join(xml_folder, filename)
    
    # Escribimos el contenido final en el archivo
    with open(filepath, 'w', encoding='utf-8') as archivo:
        archivo.write(xml_final_content)
    
    return filepath

def create_patient_xml_content(perfil_paciente):
    """
    Crea el contenido XML como un string, calcula el Checksum SHA-256 de los datos
    y lo inserta en la sección de metadatos.
    """
    usuario = perfil_paciente.id_usuario
    direccion = usuario.direccion
    
    # 1. Crear la estructura XML solo con los DATOS del paciente (el "XML ORIGINAL")
    root = ET.Element('paciente')
    
    # Número de afiliación
    ET.SubElement(root, 'num_afiliacion').text = perfil_paciente.num_afiliacion
    
    # Datos personales
    datos_personales = ET.SubElement(root, 'datos_personales')
    ET.SubElement(datos_personales, 'primer_nombre').text = usuario.primer_nombre
    ET.SubElement(datos_personales, 'segundo_nombre').text = usuario.segundo_nombre or ''
    ET.SubElement(datos_personales, 'primer_apellido').text = usuario.primer_apellido
    ET.SubElement(datos_personales, 'segundo_apellido').text = usuario.segundo_apellido or ''
    nombre_completo = f"{usuario.primer_nombre} {usuario.segundo_nombre or ''} {usuario.primer_apellido} {usuario.segundo_apellido or ''}".strip().replace('  ', ' ')
    ET.SubElement(datos_personales, 'nombre_completo').text = nombre_completo
    ET.SubElement(datos_personales, 'edad').text = str(usuario.edad)
    ET.SubElement(datos_personales, 'genero').text = usuario.genero
    
    # Datos médicos
    datos_medicos = ET.SubElement(root, 'datos_medicos')
    ET.SubElement(datos_medicos, 'tipo_sangre').text = perfil_paciente.tipo_sangre or ''
    ET.SubElement(datos_medicos, 'alergias').text = perfil_paciente.alergias or ''
    
    # Contacto
    contacto = ET.SubElement(root, 'contacto')
    ET.SubElement(contacto, 'email_usuario').text = usuario.email_usuario
    ET.SubElement(contacto, 'numero_telefono').text = usuario.numero_telefono
    
    # Dirección
    direccion_elem = ET.SubElement(root, 'direccion')
    if direccion:
        ET.SubElement(direccion_elem, 'calle').text = direccion.calle
        ET.SubElement(direccion_elem, 'num_ext').text = direccion.num_ext
        ET.SubElement(direccion_elem, 'num_int').text = direccion.num_int or ''
        ET.SubElement(direccion_elem, 'colonia').text = direccion.colonia
        ET.SubElement(direccion_elem, 'ciudad').text = direccion.ciudad
        ET.SubElement(direccion_elem, 'estado').text = str(direccion.estado.id_estado)
        ET.SubElement(direccion_elem, 'c_postal').text = direccion.c_postal
        
    # 2.  CÁLCULO DEL CHECKSUM 
    
    # Convertir el XML (solo datos) a un string limpio para calcular el hash.
    core_xml_bytes = ET.tostring(root, encoding='utf-8')
    core_xml_string_for_hash = core_xml_bytes.decode('utf-8').strip()
    
    # Calcular el Checksum (SHA-256)
    checksum_calculado = calcular_hash_sha256(core_xml_string_for_hash)
    
    # 3. AÑADIR los Metadatos y el Checksum
    metadatos = ET.SubElement(root, 'metadatos')
    ET.SubElement(metadatos, 'origen').text = 'WEB'
    ET.SubElement(metadatos, 'fecha_evento').text = datetime.now().isoformat() + 'Z'
    ET.SubElement(metadatos, 'operacion').text = 'ALTA'
    
    # Inyectar el hash calculado (REEMPLAZA el código anterior de base64)
    ET.SubElement(metadatos, 'checksum').text = checksum_calculado
    
    # 4. Convertir la estructura final (root + metadatos) a string con formato
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    
    # Usamos tu lógica de formato original para el XML final
    return reparsed.toprettyxml(indent="    ", encoding=None).replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')

@api_view(['POST'])
@permission_classes([AllowAny])
def patient_register(request):
    serializer = PatientRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        perfil_paciente = serializer.save()
        
        return Response({
            'id_paciente': perfil_paciente.id_paciente,
            'num_afiliacion': perfil_paciente.num_afiliacion,
            'message': 'Paciente registrado exitosamente'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def patient_detail(request, num_afiliacion):
    perfil_paciente = get_object_or_404(PerfilPaciente, num_afiliacion=num_afiliacion)
    usuario = perfil_paciente.id_usuario
    direccion = usuario.direccion
    
    data = {
        'id_paciente': perfil_paciente.id_paciente,
        'id_usuario': usuario.id_usuario,  # Add Usuario ID for prescriptions
        'num_afiliacion': perfil_paciente.num_afiliacion,
        'primer_nombre': usuario.primer_nombre,
        'segundo_nombre': usuario.segundo_nombre,
        'primer_apellido': usuario.primer_apellido,
        'segundo_apellido': usuario.segundo_apellido,
        'edad': usuario.edad,
        'genero': usuario.genero,
        'email_usuario': usuario.email_usuario,
        'numero_telefono': usuario.numero_telefono,
        'tipo_sangre': perfil_paciente.tipo_sangre,
        'alergias': perfil_paciente.alergias,
        'calle': direccion.calle,
        'num_ext': direccion.num_ext,
        'num_int': direccion.num_int,
        'colonia': direccion.colonia,
        'estado': direccion.estado.id_estado,
        'c_postal': direccion.c_postal,
        'ciudad': direccion.ciudad
    }
    return Response(data)

@api_view(['PUT'])
@permission_classes([AllowAny])
def patient_update(request, num_afiliacion):
    perfil_paciente = get_object_or_404(PerfilPaciente, num_afiliacion=num_afiliacion)
    serializer = PatientUpdateSerializer(perfil_paciente, data=request.data)
    if serializer.is_valid():
        serializer.save()
        
        # Refresh from database
        perfil_paciente.refresh_from_db()
        
        # Create XML file for sync
        try:
            create_patient_xml(perfil_paciente)
        except Exception as e:
            print(f"Error creating XML: {e}")
        
        return Response({
            'num_afiliacion': perfil_paciente.num_afiliacion,
            'message': 'Paciente actualizado exitosamente'
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def patient_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return Response({'error': 'Parámetro de búsqueda requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Search by name or email
    usuarios = Usuario.objects.filter(
        models.Q(primer_nombre__icontains=query) |
        models.Q(primer_apellido__icontains=query) |
        models.Q(email_usuario__icontains=query)
    ).filter(perfil_paciente__isnull=False)[:10]  # Limit to 10 results
    
    results = []
    for usuario in usuarios:
        perfil = usuario.perfil_paciente
        results.append({
            'num_afiliacion': perfil.num_afiliacion,
            'nombre_completo': f"{usuario.primer_nombre} {usuario.primer_apellido}",
            'email_usuario': usuario.email_usuario
        })
    
    return Response(results)

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_patient_to_drive(request):
    num_afiliacion = request.data.get('num_afiliacion')
    if not num_afiliacion:
        return Response({'error': 'num_afiliacion requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        perfil_paciente = PerfilPaciente.objects.select_related('id_usuario', 'id_usuario__direccion', 'id_usuario__direccion__estado').get(num_afiliacion=num_afiliacion)
        
        # Create XML with fresh data from database
        xml_content = create_patient_xml_content(perfil_paciente)
        
        return Response({
            'xml_content': xml_content,
            'filename': f"paciente_{perfil_paciente.id_usuario.primer_nombre}_{perfil_paciente.id_usuario.primer_apellido}_{perfil_paciente.num_afiliacion}.xml",
            'message': 'XML generado correctamente'
        })
    except PerfilPaciente.DoesNotExist:
        return Response({'error': 'Paciente no encontrado'}, status=status.HTTP_404_NOT_FOUND)