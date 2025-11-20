from django.contrib import admin
from .models import Medicamento, PerfilMedico, Receta, RecetaMedicamento, EnviosEmail

@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'via_administracion', 'formato', 'activo', 'fecha_creacion']
    list_filter = ['via_administracion', 'formato', 'activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']

@admin.register(PerfilMedico)
class PerfilMedicoAdmin(admin.ModelAdmin):
    list_display = ['get_nombre', 'get_primer_apellido', 'cedula_profesional', 'especialidad', 'get_activo']
    list_filter = ['especialidad', 'id_usuario__esta_activo']
    search_fields = ['id_usuario__primer_nombre', 'id_usuario__primer_apellido', 'cedula_profesional']
    ordering = ['id_usuario__primer_apellido', 'id_usuario__primer_nombre']
    
    def get_nombre(self, obj):
        return obj.id_usuario.primer_nombre
    get_nombre.short_description = 'Nombre'
    
    def get_primer_apellido(self, obj):
        return obj.id_usuario.primer_apellido
    get_primer_apellido.short_description = 'Apellido'
    
    def get_activo(self, obj):
        return obj.id_usuario.esta_activo
    get_activo.short_description = 'Activo'
    get_activo.boolean = True

class RecetaMedicamentoInline(admin.TabularInline):
    model = RecetaMedicamento
    extra = 1

@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_paciente_nombre', 'get_medico_nombre', 'diagnostico', 'fecha_creacion']
    list_filter = ['fecha_creacion', 'medico']
    search_fields = ['paciente__primer_nombre', 'paciente__primer_apellido', 'diagnostico']
    inlines = [RecetaMedicamentoInline]
    ordering = ['-fecha_creacion']
    
    def get_paciente_nombre(self, obj):
        return f"{obj.paciente.primer_nombre} {obj.paciente.primer_apellido}"
    get_paciente_nombre.short_description = 'Paciente'
    
    def get_medico_nombre(self, obj):
        return f"Dr. {obj.medico.id_usuario.primer_nombre} {obj.medico.id_usuario.primer_apellido}"
    get_medico_nombre.short_description = 'Médico'

@admin.register(EnviosEmail)
class EnviosEmailAdmin(admin.ModelAdmin):
    list_display = ['id_envio', 'get_receta_id', 'destinatario', 'tipo_email', 'estado', 'fecha_envio']
    list_filter = ['tipo_email', 'estado', 'fecha_envio']
    search_fields = ['destinatario', 'asunto']
    ordering = ['-fecha_envio']
    
    def get_receta_id(self, obj):
        return f"Receta #{obj.receta.id}"
    get_receta_id.short_description = 'Receta'