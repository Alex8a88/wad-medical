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
            response = super().create(request, *args, **kwargs)
            print(f"Prescription created successfully: {response.data}")
            return response
        except Exception as e:
            print(f"Error creating prescription: {e}")
            return Response(
                {'error': str(e)}, 
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
    """Send prescription via email"""
    print(f"Email endpoint called for receta_id: {receta_id}")
    try:
        receta = get_object_or_404(Receta, id=receta_id)
        print(f"Receta found: {receta}")
        
        # Prepare receta info for email service
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