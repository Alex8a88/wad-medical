import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Box,
  TextField,
  Button,
  Tooltip,
  Alert,
  CircularProgress,
  MenuItem,
  Typography
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFileMedical, faSearch, faPaperPlane, faPlus } from '@fortawesome/free-solid-svg-icons';
import PatientHeader from './PatientHeader';
import PatientSummary from './PatientSummary';
import DoctorSummary from './DoctorSummary';
import PrescripcionForm from './PrescripcionForm';

const GenerarReceta: React.FC = () => {
  const [numAfiliacion, setNumAfiliacion] = useState('');
  const [hasError, setHasError] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [loading, setLoading] = useState(false);
  const [patientFound, setPatientFound] = useState(false);
  const [patientData, setPatientData] = useState({
    id_paciente: null,
    id_usuario: null,
    primer_nombre: '',
    segundo_nombre: '',
    primer_apellido: '',
    segundo_apellido: '',
    edad: '',
    genero: '',
    email_usuario: '',
    alergias: '',
    tipo_sangre: ''
  });
  const [prescripcionLoading, setPrescripcionLoading] = useState(false);
  const [prescripcionMessage, setPrescripcionMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [recetaGenerada, setRecetaGenerada] = useState(false);
  const [recetaId, setRecetaId] = useState<number | null>(null);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailMessage, setEmailMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [doctores, setDoctores] = useState<any[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState('');
  const [selectedDoctor, setSelectedDoctor] = useState<any>(null);

  const handleSearch = async () => {
    setLoading(true);
    setSearchError('');
    
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/patients/${numAfiliacion}/`);
      if (!response.ok) {
        if (response.status === 404) {
          setSearchError('El Número de Afiliación que ha buscado no pertenece a un paciente existente/activo. Intente nuevamente con otro.');
        } else {
          setSearchError('Error al buscar el paciente. Intente nuevamente.');
        }
        setPatientFound(false);
        return;
      }
      
      const data = await response.json();
      console.log('Patient found:', data);
      
      setPatientData({
        id_paciente: data.id_paciente,
        id_usuario: data.id_usuario,
        primer_nombre: data.primer_nombre || '',
        segundo_nombre: data.segundo_nombre || '',
        primer_apellido: data.primer_apellido || '',
        segundo_apellido: data.segundo_apellido || '',
        edad: data.edad?.toString() || '',
        genero: data.genero || '',
        email_usuario: data.email_usuario || '',
        alergias: data.alergias || '',
        tipo_sangre: data.tipo_sangre || ''
      });
      
      setPatientFound(true);
      
    } catch (error) {
      console.error('Search error:', error);
      setSearchError('Error de conexión. Intente nuevamente.');
      setPatientFound(false);
    } finally {
      setLoading(false);
    }
  };

  const handlePrescripcionSubmit = async (prescripcionData: any) => {
    if (!selectedDoctorId) {
      setPrescripcionMessage({ type: 'error', text: 'Por favor seleccione un doctor.' });
      return;
    }
    
    setPrescripcionLoading(true);
    setPrescripcionMessage(null);
    
    try {
      // Add doctor and patient IDs to prescription data
      const prescriptionPayload = {
        ...prescripcionData,
        medico: parseInt(selectedDoctorId),
        paciente: patientData.id_usuario // Use Usuario ID for prescription
      };
      
      console.log('Sending prescription payload:', prescriptionPayload);
      
      const response = await fetch('http://127.0.0.1:8000/api/prescriptions/recetas/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(prescriptionPayload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al generar la receta');
      }

      const result = await response.json();
      console.log('Prescription created:', result);
      
      const recetaIdFromResponse = result.id;
      console.log('Setting recetaId to:', recetaIdFromResponse);
      setRecetaId(recetaIdFromResponse);
      setRecetaGenerada(true);
      setPrescripcionMessage({ type: 'success', text: 'Receta generada exitosamente' });
    } catch (error) {
      console.error('Prescription generation error:', error);
      setPrescripcionMessage({ 
        type: 'error', 
        text: error instanceof Error ? error.message : 'Error al generar la receta. Intente nuevamente.' 
      });
    } finally {
      setPrescripcionLoading(false);
    }
  };

  const handleEnviarReceta = async () => {
    if (!recetaId) {
      console.log('No recetaId available');
      return;
    }
    
    console.log('Sending email for receta ID:', recetaId);
    setEmailLoading(true);
    setEmailMessage(null);
    
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/prescriptions/recetas/${recetaId}/enviar/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      
      console.log('Email response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al enviar la receta');
      }

      const result = await response.json();
      console.log('Email sent:', result);
      
      setEmailMessage({ type: 'success', text: 'Receta enviada por email exitosamente' });
    } catch (error) {
      console.error('Email sending error:', error);
      setEmailMessage({ 
        type: 'error', 
        text: error instanceof Error ? error.message : 'Error al enviar la receta. Intente nuevamente.' 
      });
    } finally {
      setEmailLoading(false);
    }
  };

  const handleNuevaReceta = () => {
    setNumAfiliacion('');
    setPatientFound(false);
    setRecetaGenerada(false);
    setRecetaId(null);
    setPrescripcionMessage(null);
    setEmailMessage(null);
    setSearchError('');
    setHasError(false);
    setSelectedDoctorId('');
    setSelectedDoctor(null);
  };

  const fetchDoctores = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/prescriptions/medicos/');
      if (response.ok) {
        const data = await response.json();
        setDoctores(data);
      }
    } catch (error) {
      console.error('Error fetching doctors:', error);
    }
  };

  const handleDoctorChange = (doctorId: string) => {
    setSelectedDoctorId(doctorId);
    const doctor = doctores.find(d => (d.id_medico || d.id)?.toString() === doctorId);
    setSelectedDoctor(doctor);
  };

  useEffect(() => {
    fetchDoctores();
  }, []);

  const handleBlur = () => {
    if (numAfiliacion.length > 0 && numAfiliacion.length !== 8) {
      setHasError(true);
    } else {
      setHasError(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleBlur();
      if (numAfiliacion.length === 8) {
        handleSearch();
      }
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={0} sx={{ 
        p: 4, 
        backgroundColor: 'white',
        border: '1px solid #e1e8ed',
        borderRadius: 2
      }}>
        <PatientHeader icon={faFileMedical} title="Generar Receta" />
        
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, mb: 4 }}>
          <TextField
            label="Número de Afiliación"
            value={numAfiliacion}
            onChange={(e) => {
              setNumAfiliacion(e.target.value.replace(/[^0-9]/g, '').slice(0, 8));
              setHasError(false);
              setPatientFound(false);
              setRecetaGenerada(false);
              setRecetaId(null);
              setPrescripcionMessage(null);
              setEmailMessage(null);
              setSelectedDoctorId('');
              setSelectedDoctor(null);
            }}
            onBlur={handleBlur}
            onKeyPress={handleKeyPress}
            variant="outlined"
            inputProps={{ maxLength: 8 }}
            error={hasError}
            helperText={hasError ? "El número de afiliación no sigue el formato correcto. Asegúrese que sean sus 8 dígitos numéricos." : `${numAfiliacion.length}/8`}
            sx={{ width: '200px' }}
          />
          <Tooltip 
            title={numAfiliacion.length !== 8 ? "El número de afiliación no sigue el formato correcto. Asegúrese que sean sus 8 dígitos numéricos." : ""}
            arrow
          >
            <span>
              <Button
                variant="contained"
                onClick={handleSearch}
                disabled={numAfiliacion.length !== 8 || loading}
                startIcon={loading ? <CircularProgress size={16} /> : <FontAwesomeIcon icon={faSearch} />}
                sx={{ px: 3, py: 1.5 }}
              >
                {loading ? 'Buscando...' : 'Buscar Paciente'}
              </Button>
            </span>
          </Tooltip>
          
          {searchError && (
            <Alert severity="error" sx={{ mt: 2, maxWidth: '500px' }}>
              {searchError}
            </Alert>
          )}
        </Box>
        
        {patientFound && (
          <>
            <PatientSummary patientData={patientData} />
            
            {/* Doctor Selection */}
            <Paper elevation={0} sx={{ 
              p: 3, 
              mb: 3,
              backgroundColor: 'white',
              border: '1px solid #e1e8ed',
              borderRadius: 2
            }}>
              <Typography variant="h6" sx={{ mb: 2, color: '#1976d2' }}>
                Seleccionar Doctor
              </Typography>
              <TextField
                select
                fullWidth
                label="Doctor"
                value={selectedDoctorId}
                onChange={(e) => handleDoctorChange(e.target.value)}
                required
                sx={{ maxWidth: '400px' }}
              >
                {doctores.map((doctor) => (
                  <MenuItem key={doctor.id_medico || doctor.id} value={(doctor.id_medico || doctor.id)?.toString() || ''}>
                    Dr. {doctor.nombre} {doctor.primer_apellido} - {doctor.cedula_profesional}
                  </MenuItem>
                ))}
              </TextField>
            </Paper>
            
            {selectedDoctor && <DoctorSummary doctorData={selectedDoctor} />}
            
            <PrescripcionForm 
              onSubmit={handlePrescripcionSubmit}
              loading={prescripcionLoading}
              message={prescripcionMessage}
              disabled={recetaGenerada || !selectedDoctorId}
            />
            
            {patientFound && selectedDoctor && (
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 3 }}>
                <Button
                  variant="contained"
                  onClick={handleEnviarReceta}
                  disabled={!recetaGenerada || emailLoading}
                  startIcon={emailLoading ? <CircularProgress size={16} /> : <FontAwesomeIcon icon={faPaperPlane} />}
                  sx={{ px: 4, py: 1.5 }}
                >
                  {emailLoading ? 'Enviando...' : 'Mandar Receta'}
                </Button>
                
                <Button
                  variant="outlined"
                  onClick={handleNuevaReceta}
                  disabled={!recetaGenerada}
                  startIcon={<FontAwesomeIcon icon={faPlus} />}
                  sx={{ px: 4, py: 1.5 }}
                >
                  Generar Nueva Receta
                </Button>
              </Box>
            )}
            
            {emailMessage && (
              <Alert severity={emailMessage.type} sx={{ mt: 3 }}>
                {emailMessage.text}
              </Alert>
            )}
          </>
        )}
      </Paper>
    </Container>
  );
};

export default GenerarReceta;