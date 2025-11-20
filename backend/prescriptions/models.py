from django.db import models
from users.models import Usuario

class Medicamento(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    via_administracion = models.CharField(
        max_length=20,
        choices=[
            ('oral', 'Oral'),
            ('topica', 'Tópica'),
            ('inyectable', 'Inyectable'),
            ('gaseosa', 'Gaseosa'),
            ('vaginal', 'Vaginal'),
            ('rectal', 'Rectal'),
        ],
        blank=True,
        null=True
    )
    formato = models.CharField(
        max_length=20,
        choices=[
            ('solido', 'Sólido'),
            ('semisolido', 'Semisólido'),
            ('liquido', 'Líquido'),
            ('gaseoso', 'Gaseoso'),
        ],
        blank=True,
        null=True
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medicamentos'
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'

    def __str__(self):
        return self.nombre

class PerfilMedico(models.Model):
    id_medico = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    cedula_profesional = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'perfil_medicos'
        verbose_name = 'Perfil Médico'
        verbose_name_plural = 'Perfiles Médicos'

    def __str__(self):
        return f"Dr. {self.id_usuario.primer_nombre} {self.id_usuario.primer_apellido}"

class Receta(models.Model):
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='recetas')
    medico = models.ForeignKey(PerfilMedico, on_delete=models.CASCADE, related_name='recetas')
    diagnostico = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recetas'
        verbose_name = 'Receta'
        verbose_name_plural = 'Recetas'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Receta #{self.id} - {self.paciente.primer_nombre} {self.paciente.primer_apellido}"

class EnviosEmail(models.Model):
    TIPO_EMAIL_CHOICES = [
        ('PDF', 'PDF'),
        ('PASSWORD', 'Password'),
    ]
    
    ESTADO_CHOICES = [
        ('EXITOSO', 'Exitoso'),
        ('ERROR', 'Error'),
    ]
    
    id_envio = models.AutoField(primary_key=True)
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='envios_email')
    destinatario = models.EmailField(max_length=250)
    tipo_email = models.CharField(max_length=10, choices=TIPO_EMAIL_CHOICES)
    asunto = models.CharField(max_length=250)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    mensaje_error = models.TextField(blank=True, null=True)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'envios_email'
        verbose_name = 'Envío de Email'
        verbose_name_plural = 'Envíos de Email'
    
    def __str__(self):
        return f"Envío {self.id_envio} - {self.tipo_email} - {self.estado}"

class RecetaMedicamento(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='medicamentos')
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE)
    dosis = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=100)
    instrucciones_adicionales = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'receta_medicamentos'
        verbose_name = 'Medicamento de Receta'
        verbose_name_plural = 'Medicamentos de Receta'
        unique_together = ['receta', 'medicamento']

    def __str__(self):
        return f"{self.medicamento.nombre} - {self.dosis}"