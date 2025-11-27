from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
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
        try:
            # 1. Crear Receta
            response = super().create(request, *args, **kwargs)
            receta_id = response.data.get('id_receta') or response.data.get('id')
            receta = Receta.objects.get(pk=receta_id)
            
            print(f"✅ Receta {receta.id} creada. Subiendo XML...")

            # 2. Subir XML (Respaldo al crear)
            try:
                xml_path = create_prescription_xml(receta)
                filename = os.path.basename(xml_path)
                upload_xml_to_drive(xml_path, filename)
            except Exception as e:
                print(f"⚠️ Error subiendo XML al crear: {e}")

            return response
        except Exception as e:
            print(f"Error creating prescription: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RecetaDetailView(generics.RetrieveAPIView):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer

@api_view(['GET'])
def recetas_by_patient(request, num_afiliacion):
    try:
        from patients.models import PerfilPaciente
        perfil = get_object_or_404(PerfilPaciente, num_afiliacion=num_afiliacion)
        recetas = Receta.objects.filter(paciente=perfil.usuario)
        serializer = RecetaSerializer(recetas, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def doctor_register(request):
    serializer = DoctorRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        medico = serializer.save()
        return Response({'id': medico.id_medico, 'message': 'Doctor registrado'}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def enviar_receta_email(request, receta_id):
    """
    Envía el PDF por correo Y asegura que el XML esté en Drive.
    """
    print(f"📧 Endpoint Email llamado para receta_id: {receta_id}")
    try:
        receta = get_object_or_404(Receta, id=receta_id)
        
        # ==================================================================
        # 🚀 PASO CRÍTICO AGREGADO: Generar y Subir XML también al enviar
        # ==================================================================
        print("🔄 Asegurando subida de XML a Drive...")
        try:
            xml_path = create_prescription_xml(receta)
            filename = os.path.basename(xml_path)
            file_id = upload_xml_to_drive(xml_path, filename)
            if file_id:
                print(f"✅ XML sincronizado en Drive con ID: {file_id}")
            else:
                print("⚠️ No se pudo obtener ID del XML subido (pero PDF seguirá)")
        except Exception as xml_e:
            print(f"❌ Error auxiliar subiendo XML: {xml_e}")
        # ==================================================================

        # Preparar datos para el PDF/Email
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
        
        # Enviar Email (Esto genera y sube el PDF)
        success, message = enviar_receta_por_email(receta_info)
        
        if success:
            return Response({'message': message})
        else:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({'error': str(e)}, status=500)