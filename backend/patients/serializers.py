from rest_framework import serializers
from django.db import transaction
from .models import PerfilPaciente
from users.models import Usuario, Direcciones, CatalogoEstados

class PatientRegistrationSerializer(serializers.Serializer):
    # Usuario fields
    primer_nombre = serializers.CharField(max_length=100)
    segundo_nombre = serializers.CharField(max_length=100, required=False, allow_blank=True)
    primer_apellido = serializers.CharField(max_length=100)
    segundo_apellido = serializers.CharField(max_length=100, required=False, allow_blank=True)
    edad = serializers.IntegerField()
    genero = serializers.CharField(max_length=1)
    email_usuario = serializers.EmailField(max_length=250)
    numero_telefono = serializers.CharField(max_length=20)
    
    # Direcciones fields
    calle = serializers.CharField(max_length=150)
    num_ext = serializers.CharField(max_length=10)
    num_int = serializers.CharField(max_length=10, required=False, allow_blank=True)
    colonia = serializers.CharField(max_length=150)
    estado = serializers.IntegerField()  # FK to CatalogoEstados
    c_postal = serializers.CharField(max_length=5)
    ciudad = serializers.CharField(max_length=100)
    
    def validate_estado(self, value):
        try:
            CatalogoEstados.objects.get(id_estado=value)
            return value
        except CatalogoEstados.DoesNotExist:
            raise serializers.ValidationError("Estado no válido")
    
    def validate_email_usuario(self, value):
        if Usuario.objects.filter(email_usuario=value).exists():
            raise serializers.ValidationError("Este email ya está registrado")
        return value
    
    # PerfilPaciente fields
    tipo_sangre = serializers.CharField(max_length=3, required=False, allow_blank=True)
    alergias = serializers.CharField(required=False, allow_blank=True)
    
    @transaction.atomic
    def create(self, validated_data):
        # Validate estado exists
        try:
            estado_instance = CatalogoEstados.objects.get(id_estado=validated_data['estado'])
        except CatalogoEstados.DoesNotExist:
            raise serializers.ValidationError({"estado": "Estado no válido"})
        
        # Double-check email uniqueness
        if Usuario.objects.filter(email_usuario=validated_data['email_usuario']).exists():
            raise serializers.ValidationError({"email_usuario": "Este email ya está registrado"})
        
        # Create Usuario
        usuario_data = {
            'primer_nombre': validated_data['primer_nombre'],
            'segundo_nombre': validated_data.get('segundo_nombre', ''),
            'primer_apellido': validated_data['primer_apellido'],
            'segundo_apellido': validated_data.get('segundo_apellido', ''),
            'edad': validated_data['edad'],
            'genero': validated_data['genero'],
            'email_usuario': validated_data['email_usuario'],
            'numero_telefono': validated_data['numero_telefono'],
        }
        
        usuario = Usuario.objects.create(**usuario_data)
        
        # Create Direcciones
        direccion_data = {
            'id_usuario': usuario,
            'calle': validated_data['calle'],
            'num_ext': validated_data['num_ext'],
            'num_int': validated_data.get('num_int', ''),
            'colonia': validated_data['colonia'],
            'estado': estado_instance,
            'c_postal': validated_data['c_postal'],
            'ciudad': validated_data['ciudad']
        }
        
        Direcciones.objects.create(**direccion_data)
        
        # Create PerfilPaciente (num_afiliacion will be auto-generated in save method)
        perfil_paciente = PerfilPaciente(
            id_usuario=usuario,
            tipo_sangre=validated_data.get('tipo_sangre', ''),
            alergias=validated_data.get('alergias', ''),
        )
        perfil_paciente.save()  # This will trigger the auto-generation of num_afiliacion
        
        return perfil_paciente

class PatientUpdateSerializer(serializers.Serializer):
    # Usuario fields
    primer_nombre = serializers.CharField(max_length=100)
    segundo_nombre = serializers.CharField(max_length=100, required=False, allow_blank=True)
    primer_apellido = serializers.CharField(max_length=100)
    segundo_apellido = serializers.CharField(max_length=100, required=False, allow_blank=True)
    edad = serializers.IntegerField()
    genero = serializers.CharField(max_length=1)
    email_usuario = serializers.EmailField(max_length=250)
    numero_telefono = serializers.CharField(max_length=20)
    
    # Direcciones fields
    calle = serializers.CharField(max_length=150)
    num_ext = serializers.CharField(max_length=10)
    num_int = serializers.CharField(max_length=10, required=False, allow_blank=True)
    colonia = serializers.CharField(max_length=150)
    estado = serializers.IntegerField()  # FK to CatalogoEstados
    c_postal = serializers.CharField(max_length=5)
    ciudad = serializers.CharField(max_length=100)
    
    # PerfilPaciente fields
    tipo_sangre = serializers.CharField(max_length=3, required=False, allow_blank=True)
    alergias = serializers.CharField(required=False, allow_blank=True)
    
    def validate_email_usuario(self, value):
        # Check if email is already used by another patient
        current_patient = self.instance
        if Usuario.objects.filter(email_usuario=value).exclude(id_usuario=current_patient.id_usuario.id_usuario).exists():
            raise serializers.ValidationError("Este email ya está registrado por otro usuario")
        return value
    
    def validate_estado(self, value):
        try:
            CatalogoEstados.objects.get(id_estado=value)
            return value
        except CatalogoEstados.DoesNotExist:
            raise serializers.ValidationError("Estado no válido")
    
    @transaction.atomic
    def update(self, instance, validated_data):
        # Get estado instance
        try:
            estado_instance = CatalogoEstados.objects.get(id_estado=validated_data['estado'])
        except CatalogoEstados.DoesNotExist:
            raise serializers.ValidationError({"estado": "Estado no válido"})
        
        # Update Usuario
        usuario = instance.id_usuario
        usuario.primer_nombre = validated_data['primer_nombre']
        usuario.segundo_nombre = validated_data.get('segundo_nombre', '')
        usuario.primer_apellido = validated_data['primer_apellido']
        usuario.segundo_apellido = validated_data.get('segundo_apellido', '')
        usuario.edad = validated_data['edad']
        usuario.genero = validated_data['genero']
        usuario.email_usuario = validated_data['email_usuario']
        usuario.numero_telefono = validated_data['numero_telefono']
        usuario.save()
        
        # Update Direcciones
        direccion = usuario.direccion
        direccion.calle = validated_data['calle']
        direccion.num_ext = validated_data['num_ext']
        direccion.num_int = validated_data.get('num_int', '')
        direccion.colonia = validated_data['colonia']
        direccion.estado = estado_instance
        direccion.c_postal = validated_data['c_postal']
        direccion.ciudad = validated_data['ciudad']
        direccion.save()
        
        # Update PerfilPaciente
        instance.tipo_sangre = validated_data.get('tipo_sangre', '')
        instance.alergias = validated_data.get('alergias', '')
        instance.save()
        
        return instance