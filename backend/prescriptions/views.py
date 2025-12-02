from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction # Importante para deshacer cambios si falla
from .models import Medicamento, PerfilMedico, Receta, RecetaMedicamento
from .serializers import (
    MedicamentoSerializer, 
    MedicoSerializer, 
    RecetaSerializer, 
    CreateRecetaSerializer,
    DoctorRegistrationSerializer
)
from .email_service import enviar_receta_por_email
import os

# --- IMPORTACIONES CLAVE ---
from .utils import create_prescription_xml 
from .drive_utils import upload_xml_to_drive
# ---------------------------

class MedicamentoListCreateView(generics.ListCreateAPIView):
    queryset = Medicamento.objects.filter(activo=True)
    serializer_class = MedicamentoSerializer

class MedicamentoDetailView(generics.RetrieveUpdateAPIView):
    queryset = Medicamento.objects.all()
    serializer_class = MedicamentoSerializer

class MedicoListView(generics.ListAPIView):
    queryset = PerfilMedico.objects.filter(id_usuario__esta_activo=True)
    serializer_class = MedicoSerializer

class RecetaListCreateView(generics.ListCreateAPIView):
    queryset = Receta.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRecetaSerializer
        return RecetaSerializer
    
    def create(self, request, *args, **kwargs):
        # Usamos una transacción atómica: "O todo se guarda bien, o nada se guarda"
        try:
            with transaction.atomic():
                # 1. Crear Receta en BD (Tentativo)
                response = super().create(request, *args, **kwargs)
                
                receta_id = response.data.get('id_receta') or response.data.get('id')
                receta = Receta.objects.get(pk=receta_id)
                
                print(f"⏳ Receta {receta.id} creada en BD. Validando estructura...")

                # 2. Generar XML y Validar XSD
                # Si create_prescription_xml falla (por XSD), lanzará una excepción
                # y la transacción se revertirá automáticamente.
                xml_path = create_prescription_xml(receta)
                
                if not xml_path:
                    raise ValueError("No se pudo generar el archivo XML (Error desconocido)")
                
                filename = os.path.basename(xml_path)
                print(f"✅ XML Validado y Generado: {filename}")
                
                # 3. Subir a Drive
                print(f"🚀 Subiendo XML a Drive...")
                file_id = upload_xml_to_drive(xml_path, filename)
                
                if file_id:
                    print(f"☁️ ¡SUBIDA XML EXITOSA! ID: {file_id}")
                else:
                    # Opcional: Si falla Drive, ¿quieres cancelar la receta?
                    # Si sí, descomenta la siguiente línea:
                    # raise ValueError("Error subiendo a Google Drive. Revise la conexión.")
                    print("⚠️ Advertencia: XML generado pero no subido a Drive.")

                return response

        except Exception as e:
            print(f"❌ Error Estricto: {e}")
            # Como usamos transaction.atomic, la receta se borra de la BD automáticamente aquí.
            
            # Devolvemos el error al Frontend para que lo muestre en rojo
            return Response(
                {'error': str(e)}, # Aquí irá el mensaje "XML Inválido..."
                status=status.HTTP_400_BAD_REQUEST
            )

class RecetaDetailView(generics.RetrieveAPIView):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer

@api_view(['GET'])
def recetas_by_patient(request, num_afiliacion):
    """Get all prescriptions for a specific patient by num_afiliacion"""
    try:
        from patients.models import PerfilPaciente
        perfil = get_object_or_404(PerfilPaciente, num_afiliacion=num_afiliacion)
        recetas = Receta.objects.filter(paciente=perfil.usuario)
        serializer = RecetaSerializer(recetas, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def doctor_register(request):
    """Register a new doctor"""
    serializer = DoctorRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        medico = serializer.save()
        return Response({
            'id': medico.id_medico,
            'cedula_profesional': medico.cedula_profesional,
            'message': 'Doctor registrado exitosamente'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def enviar_receta_email(request, receta_id):
    """
    Envía el PDF por correo.
    Nota: Este endpoint asume que la receta YA existe y fue validada al crearse.
    """
    print(f"Email endpoint called for receta_id: {receta_id}")
    try:
        receta = get_object_or_404(Receta, id=receta_id)
        
        # Preparar datos...
        receta_info = {
            'id': receta.id,
            'paciente_nombre': f"{receta.paciente.primer_nombre} {receta.paciente.primer_apellido}",
            'paciente_edad': receta.paciente.edad,
            'paciente_genero': receta.paciente.genero,
            'paciente_email': receta.paciente.email_usuario,
            'medico_nombre': f"Dr. {receta.medico.id_usuario.primer_nombre} {receta.medico.id_usuario.primer_apellido}",
            'diagnostico': receta.diagnostico,
            'fecha_creacion': receta.fecha_creacion,
            'medicamentos': [{
                'medicamento_nombre': rm.medicamento.nombre,
                'dosis': rm.dosis,
                'frecuencia': rm.frecuencia
            } for rm in receta.medicamentos.all()]
        }
        
        print(f"Calling email service with receta_info: {receta_info}")
        success, message = enviar_receta_por_email(receta_info)
        print(f"Email service result: success={success}, message={message}")
        
        if success:
            return Response({'message': message})
        else:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': f'Error enviando receta: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )