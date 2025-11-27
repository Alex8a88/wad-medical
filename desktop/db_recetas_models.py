from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
# Importamos la 'Base' y el 'engine' de tu archivo db.py existente
# Esto conecta las nuevas tablas a la misma base de datos 'recetas.db'
from db import Base, engine 

class RecetaLocal(Base):
    __tablename__ = 'recetas_local'

    id_receta = Column(Integer, primary_key=True, autoincrement=True)
    folio_web = Column(String(50), unique=True) # ID original del XML (backend)
    
    # Vinculamos con la tabla perfil_paciente que ya existe en db.py
    num_afiliacion = Column(String(20), ForeignKey('perfil_paciente.num_afiliacion'))
    
    nombre_doctor = Column(String(100))
    cedula_doctor = Column(String(20))
    
    diagnostico = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.now) # Cuándo se creó en Web
    fecha_importacion = Column(DateTime, default=datetime.now) # Cuándo llegó aquí
    
    # Control para saber si ya se imprimió en papel
    impresa = Column(Boolean, default=False)
    
    # Control de seguridad (si el XML venía alterado)
    integridad_valida = Column(Boolean, default=True)

    # Relación: Una receta tiene muchos medicamentos
    medicamentos = relationship("MedicamentoRecetaLocal", back_populates="receta", cascade="all, delete-orphan")

class MedicamentoRecetaLocal(Base):
    __tablename__ = 'medicamentos_receta_local'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_receta = Column(Integer, ForeignKey('recetas_local.id_receta'))
    
    nombre_medicamento = Column(String(150))
    dosis = Column(String(100))
    frecuencia = Column(String(100))
    duracion = Column(String(100))
    notas = Column(Text)

    # Relación inversa
    receta = relationship("RecetaLocal", back_populates="medicamentos")

def init_recetas_db():
    """
    Función para crear SOLO las tablas nuevas en la base de datos.
    No borra nada de lo anterior.
    """
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Si ejecutas este archivo directamente, creará las tablas.
    print("Creando tablas de recetas en recetas.db...")
    init_recetas_db()
    print("✅ Tablas de recetas creadas exitosamente.")