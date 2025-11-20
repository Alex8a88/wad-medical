from django.db import models
from django.core.validators import RegexValidator
from users.models import Usuario
import random
import string

class PerfilPaciente(models.Model):
    TIPO_SANGRE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    id_paciente = models.AutoField(primary_key=True)
    num_afiliacion = models.CharField(
        max_length=8, 
        unique=True,
        validators=[RegexValidator(regex=r'^\d{8}$', message='Debe ser exactamente 8 dígitos')]
    )
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo_sangre = models.CharField(max_length=3, choices=TIPO_SANGRE_CHOICES, blank=True)
    alergias = models.TextField(blank=True)
    
    class Meta:
        db_table = 'perfil_paciente'
    
    def save(self, *args, **kwargs):
        if not self.num_afiliacion:
            self.num_afiliacion = self.generate_unique_num_afiliacion()
        super().save(*args, **kwargs)
    
    def generate_unique_num_afiliacion(self):
        while True:
            num_afiliacion = ''.join(random.choices(string.digits, k=8))
            if not PerfilPaciente.objects.filter(num_afiliacion=num_afiliacion).exists():
                return num_afiliacion
    
    def __str__(self):
        return f"{self.num_afiliacion} - {self.id_usuario.primer_nombre} {self.id_usuario.primer_apellido}"