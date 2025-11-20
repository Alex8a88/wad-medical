from rest_framework import serializers
from django.db import transaction
from .models import Medicamento, PerfilMedico, Receta, RecetaMedicamento
from users.models import Usuario, Direcciones, CatalogoEstados

class MedicamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicamento
        fields = ['id', 'nombre', 'descripcion', 'via_administracion', 'formato', 'activo']
    
    def validate_nombre(self, value):
        # Check for duplicate medication names (case-insensitive)
        if self.instance:
            # Update case - exclude current instance
            if Medicamento.objects.filter(nombre__iexact=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Ya existe un medicamento con este nombre")
        else:
            # Create case
            if Medicamento.objects.filter(nombre__iexact=value).exists():
                raise serializers.ValidationError("Ya existe un medicamento con este nombre")
        return value

class MedicoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='id_usuario.primer_nombre', read_only=True)
    primer_apellido = serializers.CharField(source='id_usuario.primer_apellido', read_only=True)
    segundo_apellido = serializers.CharField(source='id_usuario.segundo_apellido', read_only=True)
    
    class Meta:
        model = PerfilMedico
        fields = ['id_medico', 'nombre', 'primer_apellido', 'segundo_apellido', 'cedula_profesional', 'especialidad']

class RecetaMedicamentoSerializer(serializers.ModelSerializer):
    medicamento_nombre = serializers.CharField(source='medicamento.nombre', read_only=True)
    
    class Meta:
        model = RecetaMedicamento
        fields = ['id', 'medicamento', 'medicamento_nombre', 'dosis', 'frecuencia', 'instrucciones_adicionales']

class RecetaSerializer(serializers.ModelSerializer):
    medicamentos = RecetaMedicamentoSerializer(many=True, read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    medico_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Receta
        fields = ['id', 'paciente', 'medico', 'diagnostico', 'fecha_creacion', 'fecha_modificacion', 
                 'medicamentos', 'paciente_nombre', 'medico_nombre']
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def get_paciente_nombre(self, obj):
        return f"{obj.paciente.primer_nombre} {obj.paciente.primer_apellido}"
    
    def get_medico_nombre(self, obj):
        return f"Dr. {obj.medico.id_usuario.primer_nombre} {obj.medico.id_usuario.primer_apellido}"

class CreateRecetaSerializer(serializers.ModelSerializer):
    medicamentos = serializers.ListField(write_only=True)
    
    class Meta:
        model = Receta
        fields = ['id', 'paciente', 'medico', 'diagnostico', 'medicamentos']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        medicamentos_data = validated_data.pop('medicamentos')
        receta = Receta.objects.create(**validated_data)
        
        for med_data in medicamentos_data:
            # Find medicamento by name
            try:
                medicamento = Medicamento.objects.get(nombre=med_data['medicamento'])
                RecetaMedicamento.objects.create(
                    receta=receta,
                    medicamento=medicamento,
                    dosis=med_data['dosis'],
                    frecuencia=med_data['frecuencia']
                )
            except Medicamento.DoesNotExist:
                continue  # Skip if medication doesn't exist
        
        return receta

class DoctorRegistrationSerializer(serializers.Serializer):
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
    estado = serializers.IntegerField()
    c_postal = serializers.CharField(max_length=5)
    ciudad = serializers.CharField(max_length=100)
    
    # Medico fields
    cedula_profesional = serializers.CharField(max_length=20)
    especialidad = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # Login fields
    password = serializers.CharField(max_length=128, write_only=True)
    
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
    
    def validate_cedula_profesional(self, value):
        if PerfilMedico.objects.filter(cedula_profesional=value).exists():
            raise serializers.ValidationError("Esta cédula profesional ya está registrada")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        # Validate estado exists
        try:
            estado_instance = CatalogoEstados.objects.get(id_estado=validated_data['estado'])
        except CatalogoEstados.DoesNotExist:
            raise serializers.ValidationError({"estado": "Estado no válido"})
        
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
            'es_staff': True,
        }
        
        usuario = Usuario.objects.create_user(
            email_usuario=usuario_data['email_usuario'],
            password=validated_data['password'],
            **{k: v for k, v in usuario_data.items() if k != 'email_usuario'}
        )
        
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
        
        # Create PerfilMedico
        medico_data = {
            'id_usuario': usuario,
            'cedula_profesional': validated_data['cedula_profesional'],
            'especialidad': validated_data.get('especialidad', ''),
        }
        
        medico = PerfilMedico.objects.create(**medico_data)
        
        return medico