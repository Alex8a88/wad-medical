import React, { useState } from 'react';
import {
  Container,
  Paper,
  Box,
  Typography,
  Button
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserPlus, faCheckCircle } from '@fortawesome/free-solid-svg-icons';
import { initializeGapi, signIn, generatePatientXML, uploadToGoogleDrive } from './googleDrive';
import PatientForm from './PatientForm';
import PatientHeader from './PatientHeader';

interface PatientData {
  primer_nombre: string;
  segundo_nombre: string;
  primer_apellido: string;
  segundo_apellido: string;
  edad: string;
  genero: string;
  tipo_sangre: string;
  num_afiliacion: string;
  alergias: string;
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
}

interface FieldErrors {
  primer_nombre: boolean;
  segundo_nombre: boolean;
  primer_apellido: boolean;
  segundo_apellido: boolean;
  edad: boolean;
  genero: boolean;
  tipo_sangre: boolean;
  num_afiliacion: boolean;
  alergias: boolean;
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
}

const PatientRegistration: React.FC = () => {
  const [formData, setFormData] = useState<PatientData>({
    primer_nombre: '',
    segundo_nombre: '',
    primer_apellido: '',
    segundo_apellido: '',
    edad: '',
    genero: '',
    tipo_sangre: '',
    num_afiliacion: '',
    alergias: '',
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
    c_postal: ''
  });

  const [errors, setErrors] = useState<FieldErrors>({
    primer_nombre: false,
    segundo_nombre: false,
    primer_apellido: false,
    segundo_apellido: false,
    edad: false,
    genero: false,
    tipo_sangre: false,
    num_afiliacion: false,
    alergias: false,
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
    c_postal: false
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [showSuccessScreen, setShowSuccessScreen] = useState(false);
  const [numeroAfiliacion, setNumeroAfiliacion] = useState('');

  React.useEffect(() => {
    const initializeGoogleAPIs = async () => {
      try {
        await initializeGapi();
      } catch (error) {
        console.error('Error initializing Google APIs:', error);
      }
    };
    
    initializeGoogleAPIs();
  }, []);

  const validateForm = () => {
    const newErrors = { ...errors };
    let hasErrors = false;

    const requiredFields: (keyof PatientData)[] = [
      'primer_nombre', 'primer_apellido', 'edad', 'genero', 'tipo_sangre', 'emailUser', 'emailDomain',
      'numero_telefono', 'calle', 'num_ext', 'colonia', 'estado', 'ciudad', 'c_postal'
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
      // Save to database
      const response = await fetch('http://127.0.0.1:8000/api/patients/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al guardar en la base de datos');
      }

      const patientData = await response.json();
      setNumeroAfiliacion(patientData.num_afiliacion);

      // Show success screen
      setShowSuccessScreen(true);
      
      setFormData({
        primer_nombre: '', segundo_nombre: '', primer_apellido: '', segundo_apellido: '', edad: '', genero: '', tipo_sangre: '',
        num_afiliacion: '', alergias: '', email_usuario: '', emailUser: '', emailDomain: '', numero_telefono: '',
        calle: '', num_ext: '', num_int: '', colonia: '', estado: '', ciudad: '', c_postal: ''
      });

    } catch (error) {
      console.error('Error registering patient:', error);
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Error al registrar paciente. Intente nuevamente.' });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSuccess = async () => {
    try {
      // Upload to Google Drive when closing
      const response = await fetch('http://127.0.0.1:8000/api/patients/upload-to-drive/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ num_afiliacion: numeroAfiliacion }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Sign in to Google Drive if needed
        if (!isSignedIn) {
          await signIn();
          setIsSignedIn(true);
        }

        // Upload to Google Drive
        await uploadToGoogleDrive(data.xml_content, data.filename);
        console.log('Patient data uploaded to Google Drive successfully');
      }
    } catch (error) {
      console.error('Error uploading to Google Drive:', error);
    }
    
    setShowSuccessScreen(false);
    setNumeroAfiliacion('');
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
              ¡Paciente Registrado Exitosamente!
            </Typography>
            <Typography variant="h6" sx={{ mb: 3, color: '#333' }}>
              El paciente ha sido registrado en la base de datos y enviado a Google Drive.
            </Typography>
            <Typography variant="h5" sx={{ mb: 4, color: '#1976d2', fontWeight: 'bold' }}>
              Número de Afiliación: {numeroAfiliacion}
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={handleCloseSuccess}
              sx={{ px: 4, py: 1.5 }}
            >
              Mandar a Proxy
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
        <PatientHeader icon={faUserPlus} title="Registrar Paciente" />
        
        <PatientForm
          formData={formData}
          setFormData={setFormData}
          errors={errors}
          setErrors={setErrors}
          onSubmit={handleSubmit}
          loading={loading}
          message={message}
          buttonText="Registrar Paciente"
        />

      </Paper>
    </Container>
  );
};

export default PatientRegistration;