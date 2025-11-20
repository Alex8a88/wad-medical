from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class Grupos(models.Model):
    id_grupo = models.AutoField(primary_key=True)
    nombre_grupo = models.CharField(max_length=50, unique=True)
    
    class Meta:
        db_table = 'grupos'
    
    def __str__(self):
        return self.nombre_grupo

class CatalogoEstados(models.Model):
    id_estado = models.AutoField(primary_key=True)
    nombre_estado = models.CharField(max_length=100, unique=True)
    
    class Meta:
        db_table = 'catalogo_estados'
    
    def __str__(self):
        return self.nombre_estado

class UsuarioManager(BaseUserManager):
    def create_user(self, email_usuario, password=None, **extra_fields):
        if not email_usuario:
            raise ValueError('El email es obligatorio')
        email_usuario = self.normalize_email(email_usuario)
        user = self.model(email_usuario=email_usuario, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email_usuario, password=None, **extra_fields):
        extra_fields.setdefault('es_staff', True)
        extra_fields.setdefault('es_superusuario', True)
        extra_fields.setdefault('esta_activo', True)
        if not password:
            raise ValueError('Superuser must have a password')
        return self.create_user(email_usuario, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('X', 'No Binario'),
    ]
    
    id_usuario = models.AutoField(primary_key=True)
    email_usuario = models.EmailField(max_length=250, unique=True)
    esta_activo = models.BooleanField(default=True)
    primer_nombre = models.CharField(max_length=100)
    segundo_nombre = models.CharField(max_length=100, blank=True)
    primer_apellido = models.CharField(max_length=100)
    segundo_apellido = models.CharField(max_length=100, blank=True)
    edad = models.IntegerField()
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES)
    numero_telefono = models.CharField(max_length=20)
    es_staff = models.BooleanField(default=False)
    es_superusuario = models.BooleanField(default=False)
    grupos = models.ForeignKey(Grupos, on_delete=models.SET_NULL, null=True, blank=True)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email_usuario'
    REQUIRED_FIELDS = ['primer_nombre', 'primer_apellido', 'edad', 'genero', 'numero_telefono']
    
    class Meta:
        db_table = 'usuarios'
    
    def __str__(self):
        return f"{self.primer_nombre} {self.primer_apellido}"
    
    @property
    def is_active(self):
        return self.esta_activo
    
    @property
    def is_staff(self):
        return self.es_staff
    
    @property
    def is_superuser(self):
        return self.es_superusuario

class Direcciones(models.Model):
    id_direccion = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='direccion')
    calle = models.CharField(max_length=150)
    num_ext = models.CharField(max_length=10)
    num_int = models.CharField(max_length=10, blank=True)
    colonia = models.CharField(max_length=150)
    estado = models.ForeignKey(CatalogoEstados, on_delete=models.PROTECT)
    c_postal = models.CharField(max_length=5)
    ciudad = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'direcciones'
    
    def __str__(self):
        return f"{self.calle} {self.num_ext}, {self.colonia}"