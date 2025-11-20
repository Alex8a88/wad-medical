# db.py (SQLAlchemy models and ORM usage example)
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from config import DATABASE_URL
import random
import string

Base = declarative_base()

class Grupos(Base):
    __tablename__ = 'grupos'
    id_grupo = Column(Integer, primary_key=True)
    nombre_grupo = Column(String(50), unique=True, nullable=False)

class CatalogoEstados(Base):
    __tablename__ = 'catalogo_estados'
    id_estado = Column(Integer, primary_key=True)
    nombre_estado = Column(String(100), unique=True, nullable=False)

class Usuario(Base):
    __tablename__ = 'usuarios'
    id_usuario = Column(Integer, primary_key=True)
    email_usuario = Column(String(250), unique=True, nullable=False)
    esta_activo = Column(Boolean, default=True)
    primer_nombre = Column(String(100), nullable=False)
    segundo_nombre = Column(String(100))
    primer_apellido = Column(String(100), nullable=False)
    segundo_apellido = Column(String(100))
    edad = Column(Integer, nullable=False)
    genero = Column(String(1), nullable=False)  # M, F, X
    numero_telefono = Column(String(20), nullable=False)
    es_staff = Column(Boolean, default=False)
    es_superusuario = Column(Boolean, default=False)
    grupos = Column(Integer, ForeignKey('grupos.id_grupo'))
    
    # Relationships
    direccion = relationship('Direcciones', back_populates='usuario', uselist=False)
    perfil_paciente = relationship('PerfilPaciente', back_populates='usuario', uselist=False)
    recetas = relationship('Receta', foreign_keys='Receta.paciente')

class Direcciones(Base):
    __tablename__ = 'direcciones'
    id_direccion = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    calle = Column(String(150), nullable=False)
    num_ext = Column(String(10), nullable=False)
    num_int = Column(String(10))
    colonia = Column(String(150), nullable=False)
    estado = Column(Integer, ForeignKey('catalogo_estados.id_estado'), nullable=False)
    c_postal = Column(String(5), nullable=False)
    ciudad = Column(String(100), nullable=False)
    
    # Relationships
    usuario = relationship('Usuario', back_populates='direccion')
    estado_obj = relationship('CatalogoEstados')

class PerfilPaciente(Base):
    __tablename__ = 'perfil_paciente'
    id_paciente = Column(Integer, primary_key=True)
    num_afiliacion = Column(String(8), unique=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    tipo_sangre = Column(String(3))  # A+, A-, B+, B-, AB+, AB-, O+, O-
    alergias = Column(Text)

    # Nuevo campo: indica si el XML/JSON del paciente pasó la verificación de integridad
    integridad_valida = Column(Boolean, default=True)

    # Relationships
    usuario = relationship('Usuario', back_populates='perfil_paciente')

    def generate_unique_num_afiliacion(self, session):
        while True:
            num_afiliacion = ''.join(random.choices(string.digits, k=8))
            if not session.query(PerfilPaciente).filter_by(num_afiliacion=num_afiliacion).first():
                return num_afiliacion
    
    # Relationships
    usuario = relationship('Usuario', back_populates='perfil_paciente')
    
    def generate_unique_num_afiliacion(self, session):
        while True:
            num_afiliacion = ''.join(random.choices(string.digits, k=8))
            if not session.query(PerfilPaciente).filter_by(num_afiliacion=num_afiliacion).first():
                return num_afiliacion

class PerfilMedico(Base):
    __tablename__ = 'perfil_medicos'
    id_medico = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    cedula_profesional = Column(String(20), unique=True, nullable=False)
    especialidad = Column(String(100))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    usuario = relationship('Usuario')
    recetas = relationship('Receta', foreign_keys='Receta.medico')

class Receta(Base):
    __tablename__ = 'recetas'
    id = Column(Integer, primary_key=True)
    paciente = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    medico = Column(Integer, ForeignKey('perfil_medicos.id_medico'), nullable=False)
    diagnostico = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    paciente_obj = relationship('Usuario', overlaps='recetas')
    medico_obj = relationship('PerfilMedico', overlaps='recetas')
    medicamentos = relationship('RecetaMedicamento', back_populates='receta', cascade='all, delete-orphan')

class Medicamento(Base):
    __tablename__ = 'medicamentos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), unique=True, nullable=False)
    descripcion = Column(Text)
    via_administracion = Column(String(20))
    formato = Column(String(20))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

class RecetaMedicamento(Base):
    __tablename__ = 'receta_medicamentos'
    id = Column(Integer, primary_key=True)
    receta_id = Column(Integer, ForeignKey('recetas.id'))
    medicamento_id = Column(Integer, ForeignKey('medicamentos.id'))
    dosis = Column(String)
    frecuencia = Column(String)
    receta = relationship('Receta', back_populates='medicamentos')
    medicamento = relationship('Medicamento')

class EnviosEmail(Base):
    __tablename__ = 'envios_email'
    id_envio = Column(Integer, primary_key=True)
    receta = Column(Integer, ForeignKey('recetas.id'), nullable=False)
    destinatario = Column(String(250), nullable=False)
    tipo_email = Column(String(10), nullable=False)  # 'PDF' or 'PASSWORD'
    asunto = Column(String(250), nullable=False)
    estado = Column(String(10), nullable=False)  # 'EXITOSO', 'ERROR'
    mensaje_error = Column(Text)
    fecha_envio = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    receta_obj = relationship('Receta')

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

def buscar_paciente_por_codigo(session, num_afiliacion):
    """Find patient by num_afiliacion"""
    perfil = session.query(PerfilPaciente).filter_by(num_afiliacion=num_afiliacion).first()
    return perfil.usuario if perfil else None

def init_db():
    Base.metadata.create_all(bind=engine)

def insertar_receta(session, receta_dict):
    # Check if receta already exists by ID
    if 'id' in receta_dict:
        existing_receta = session.query(Receta).filter_by(id=receta_dict['id']).first()
        if existing_receta:
            return existing_receta  # Skip insertion if already exists

    # Find or create usuario
    paciente_data = receta_dict['paciente']
    usuario = session.query(Usuario).filter_by(email_usuario=paciente_data.get('email_usuario')).first()
    if not usuario:
        usuario = Usuario(
            email_usuario=paciente_data.get('email_usuario'),
            primer_nombre=paciente_data.get('primer_nombre'),
            segundo_nombre=paciente_data.get('segundo_nombre', ''),
            primer_apellido=paciente_data.get('primer_apellido'),
            segundo_apellido=paciente_data.get('segundo_apellido', ''),
            edad=paciente_data.get('edad'),
            genero=paciente_data.get('genero'),
            numero_telefono=paciente_data.get('numero_telefono')
        )
        session.add(usuario)
        session.flush()
        
        # Create perfil_paciente
        perfil = PerfilPaciente(
            id_usuario=usuario.id_usuario,
            tipo_sangre=paciente_data.get('tipo_sangre'),
            alergias=paciente_data.get('alergias', '')
        )
        if not perfil.num_afiliacion:
            perfil.num_afiliacion = perfil.generate_unique_num_afiliacion(session)
        session.add(perfil)
        session.flush()

    # Find PerfilMedico by cedula_profesional
    perfil_medico = session.query(PerfilMedico).filter_by(cedula_profesional=receta_dict['medico'].get('cedula')).first()
    if not perfil_medico:
        # Create usuario for medico if needed
        medico_data = receta_dict['medico']
        usuario_medico = Usuario(
            email_usuario=f"{medico_data.get('cedula')}@medico.com",  # Placeholder email
            primer_nombre=medico_data.get('nombre', ''),
            primer_apellido=medico_data.get('primer_apellido', ''),
            edad=35,  # Default age
            genero='M',  # Default gender
            numero_telefono='0000000000',  # Default phone
            es_staff=True
        )
        session.add(usuario_medico)
        session.flush()
        
        perfil_medico = PerfilMedico(
            id_usuario=usuario_medico.id_usuario,
            cedula_profesional=receta_dict['medico'].get('cedula'),
            especialidad=receta_dict['medico'].get('especialidad')
        )
        session.add(perfil_medico)
        session.flush()

    r = Receta(paciente=usuario.id_usuario, medico=perfil_medico.id_medico, diagnostico=receta_dict.get('diagnostico'), fecha_creacion=receta_dict.get('fecha'))
    session.add(r)
    session.flush()

    for med in receta_dict.get('medicamentos', []):
        # Find or create medicamento
        medicamento = session.query(Medicamento).filter_by(nombre=med.get('nombre')).first()
        if not medicamento:
            medicamento = Medicamento(nombre=med.get('nombre'))
            session.add(medicamento)
            session.flush()
        
        # Create receta-medicamento relationship
        rm = RecetaMedicamento(receta_id=r.id, medicamento_id=medicamento.id, 
                              dosis=med.get('dosis'), frecuencia=med.get('frecuencia'))
        session.add(rm)

    session.commit()
    return r

def listar_recetas_por_paciente(session, nombre_paciente):
    usuario = session.query(Usuario).filter_by(primer_nombre=nombre_paciente).first()
    if not usuario:
        return []
    resultado = []
    for r in usuario.recetas:
        resultado.append({
            'id': r.id,
            'diagnostico': r.diagnostico,
            'fecha': r.fecha_creacion,
            'medicamentos': [{'nombre': m.medicamento.nombre, 'dosis': m.dosis, 'frecuencia': m.frecuencia} for m in r.medicamentos]
        })
    return resultado

def obtener_todas_recetas(session):
    recetas = session.query(Receta).all()
    resultado = []
    for r in recetas:
        resultado.append({
            'id': r.id,
            'paciente': f"{r.paciente_obj.primer_nombre} {r.paciente_obj.primer_apellido}",
            'diagnostico': r.diagnostico,
            'fecha': r.fecha_creacion.strftime('%Y-%m-%d %H:%M') if r.fecha_creacion else 'N/A'
        })
    return resultado

def obtener_receta_por_id(session, receta_id):
    receta = session.query(Receta).filter_by(id=receta_id).first()
    if not receta:
        return None
    
    perfil_paciente = receta.paciente_obj.perfil_paciente
    num_afiliacion = perfil_paciente.num_afiliacion if perfil_paciente else 'N/A'
    
    return {
        'id': receta.id,
        'paciente': {
            'codigo': num_afiliacion,
            'nombre': receta.paciente_obj.primer_nombre,
            'primer_apellido': receta.paciente_obj.primer_apellido,
            'segundo_apellido': receta.paciente_obj.segundo_apellido,
            'edad': receta.paciente_obj.edad,
            'genero': receta.paciente_obj.genero,
            'correo': receta.paciente_obj.email_usuario
        },
        'medico': {
            'nombre': receta.medico_obj.usuario.primer_nombre,
            'cedula': receta.medico_obj.cedula_profesional
        },
        'diagnostico': receta.diagnostico,
        'fecha': receta.fecha_creacion,
        'medicamentos': [{
            'medicina': m.medicamento.nombre,
            'dosis': m.dosis,
            'frecuencia': m.frecuencia
        } for m in receta.medicamentos]
    }
