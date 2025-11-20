import React, { useState } from 'react';
import {
  Container,
  Paper,
  Box,
  Typography,
  Button
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserMd, faCheckCircle } from '@fortawesome/free-solid-svg-icons';
import DoctorForm from './DoctorForm';
import PatientHeader from './PatientHeader';

interface DoctorData {
  primer_nombre: string;
  segundo_nombre: string;
  primer_apellido: string;
  segundo_apellido: string;
  edad: string;
  genero: string;
  email_usuario: string;
  emailUser: string;
  emailDomain: string;
  numero_telefono: string;
  calle: string;
  num_ext: string;
  num_int: string;
  colonia: string;
  estado: string;
  ciudad: string;
  c_postal: string;
  cedula_profesional: string;
  especialidad: string;
  password: string;
}

interface FieldErrors {
  primer_nombre: boolean;
  segundo_nombre: boolean;
  primer_apellido: boolean;
  segundo_apellido: boolean;
  edad: boolean;
  genero: boolean;
  email_usuario: boolean;
  emailUser: boolean;
  emailDomain: boolean;
  numero_telefono: boolean;
  calle: boolean;
  num_ext: boolean;
  num_int: boolean;
  colonia: boolean;
  estado: boolean;
  ciudad: boolean;
  c_postal: boolean;
  cedula_profesional: boolean;
  especialidad: boolean;
  password: boolean;
}

const DoctorRegistration: React.FC = () => {
  const [formData, setFormData] = useState<DoctorData>({
    primer_nombre: '',
    segundo_nombre: '',
    primer_apellido: '',
    segundo_apellido: '',
    edad: '',
    genero: '',
    email_usuario: '',
    emailUser: '',
    emailDomain: '',
    numero_telefono: '',
    calle: '',
    num_ext: '',
    num_int: '',
    colonia: '',
    estado: '',
    ciudad: '',
    c_postal: '',
    cedula_profesional: '',
    especialidad: '',
    password: ''
  });

  const [errors, setErrors] = useState<FieldErrors>({
    primer_nombre: false,
    segundo_nombre: false,
    primer_apellido: false,
    segundo_apellido: false,
    edad: false,
    genero: false,
    email_usuario: false,
    emailUser: false,
    emailDomain: false,
    numero_telefono: false,
    calle: false,
    num_ext: false,
    num_int: false,
    colonia: false,
    estado: false,
    ciudad: false,
    c_postal: false,
    cedula_profesional: false,
    especialidad: false,
    password: false
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [showSuccessScreen, setShowSuccessScreen] = useState(false);
  const [cedulaProfesional, setCedulaProfesional] = useState('');

  const validateForm = () => {
    const newErrors = { ...errors };
    let hasErrors = false;

    const requiredFields: (keyof DoctorData)[] = [
      'primer_nombre', 'primer_apellido', 'edad', 'genero', 'emailUser', 'emailDomain',
      'numero_telefono', 'calle', 'num_ext', 'colonia', 'estado', 'ciudad', 'c_postal',
      'cedula_profesional', 'password'
    ];

    requiredFields.forEach(field => {
      const value = formData[field];
      const isEmpty = typeof value === 'string' ? !value.trim() : !value;
      if (isEmpty) {
        newErrors[field] = true;
        hasErrors = true;
      }
    });

    setErrors(newErrors);
    return !hasErrors;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);

    if (!validateForm()) {
      setMessage({ type: 'error', text: 'Por favor complete todos los campos obligatorios.' });
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/prescriptions/medicos/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al registrar doctor');
      }

      const doctorData = await response.json();
      setCedulaProfesional(doctorData.cedula_profesional);

      setShowSuccessScreen(true);
      
      setFormData({
        primer_nombre: '', segundo_nombre: '', primer_apellido: '', segundo_apellido: '', edad: '', genero: '',
        email_usuario: '', emailUser: '', emailDomain: '', numero_telefono: '',
        calle: '', num_ext: '', num_int: '', colonia: '', estado: '', ciudad: '', c_postal: '',
        cedula_profesional: '', especialidad: '', password: ''
      });

    } catch (error) {
      console.error('Error registering doctor:', error);
      setMessage({ 
        type: 'error', 
        text: error instanceof Error ? error.message : 'Error al registrar doctor. Intente nuevamente.' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSuccess = () => {
    setShowSuccessScreen(false);
    setCedulaProfesional('');
    setMessage(null);
  };

  if (showSuccessScreen) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper elevation={0} sx={{ 
          p: 4, 
          backgroundColor: 'white',
          border: '1px solid #e1e8ed',
          borderRadius: 2
        }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', py: 4 }}>
            <FontAwesomeIcon 
              icon={faCheckCircle} 
              style={{ 
                fontSize: '120px', 
                color: '#4caf50', 
                marginBottom: '24px' 
              }}
            />
            <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: '#4caf50' }}>
              ¡Doctor Registrado Exitosamente!
            </Typography>
            <Typography variant="h6" sx={{ mb: 3, color: '#333' }}>
              El doctor ha sido registrado en la base de datos.
            </Typography>
            <Typography variant="h5" sx={{ mb: 4, color: '#1976d2', fontWeight: 'bold' }}>
              Cédula Profesional: {cedulaProfesional}
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={handleCloseSuccess}
              sx={{ px: 4, py: 1.5 }}
            >
              Cerrar
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={0} sx={{ 
        p: 4, 
        backgroundColor: 'white',
        border: '1px solid #e1e8ed',
        borderRadius: 2
      }}>
        <PatientHeader icon={faUserMd} title="Registrar Doctor" />
        
        <DoctorForm
          formData={formData}
          setFormData={setFormData}
          errors={errors}
          setErrors={setErrors}
          onSubmit={handleSubmit}
          loading={loading}
          message={message}
          buttonText="Registrar Doctor"
        />

      </Paper>
    </Container>
  );
};

export default DoctorRegistration;