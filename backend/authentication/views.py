from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email_usuario = request.data.get('username')  # Frontend sends 'username'
    password = request.data.get('password')
    
    if not email_usuario or not password:
        return Response({'error': 'Email and password required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, username=email_usuario, password=password)
    if user and user.is_active:
        login(request, user)
        
        # Get cedula_profesional if user is a doctor
        cedula_profesional = None
        try:
            from prescriptions.models import PerfilMedico
            perfil_medico = PerfilMedico.objects.get(id_usuario=user)
            cedula_profesional = perfil_medico.cedula_profesional
        except PerfilMedico.DoesNotExist:
            pass
        
        return Response({
            'message': 'Login successful', 
            'user_id': user.id_usuario,
            'primer_nombre': user.primer_nombre,
            'nombre_completo': f"{user.primer_nombre} {user.primer_apellido}",
            'email_usuario': user.email_usuario,
            'genero': user.genero,
            'cedula_profesional': cedula_profesional
        })
    
    return Response({'error': 'Invalid credentials'}, 
                   status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logout successful'})

@api_view(['GET'])
def check_auth(request):
    if request.user.is_authenticated:
        # Get cedula_profesional if user is a doctor
        cedula_profesional = None
        try:
            from prescriptions.models import PerfilMedico
            perfil_medico = PerfilMedico.objects.get(id_usuario=request.user)
            cedula_profesional = perfil_medico.cedula_profesional
        except PerfilMedico.DoesNotExist:
            pass
        
        return Response({
            'authenticated': True, 
            'user_id': request.user.id_usuario,
            'primer_nombre': request.user.primer_nombre,
            'nombre_completo': f"{request.user.primer_nombre} {request.user.primer_apellido}",
            'email_usuario': request.user.email_usuario,
            'genero': request.user.genero,
            'cedula_profesional': cedula_profesional
        })
    return Response({'authenticated': False})