import React, { useState } from 'react';
import {
  Container,
  Paper,
  Box,
  TextField,
  Button,
  Tooltip,
  Alert,
  CircularProgress
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserEdit, faSearch } from '@fortawesome/free-solid-svg-icons';
import PatientForm from './PatientForm';
import PatientHeader from './PatientHeader';
import { initializeGapi, signIn, generatePatientXML, uploadToGoogleDrive } from './googleDrive';

const PatientUpdate: React.FC = () => {
  const [numAfiliacion, setNumAfiliacion] = useState('');
  const [hasError, setHasError] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [loading, setLoading] = useState(false);
  const [patientFound, setPatientFound] = useState(false);
  const [formData, setFormData] = useState({
    primer_nombre: '', segundo_nombre: '', primer_apellido: '', segundo_apellido: '', edad: '', genero: '', tipo_sangre: '',
    num_afiliacion: '', alergias: '', email_usuario: '', emailUser: '', emailDomain: '', numero_telefono: '',
    calle: '', num_ext: '', num_int: '', colonia: '', estado: '', ciudad: '', c_postal: ''
  });
  const [errors, setErrors] = useState({
    primer_nombre: false, segundo_nombre: false, primer_apellido: false, segundo_apellido: false, edad: false,
    genero: false, tipo_sangre: false, num_afiliacion: false, alergias: false, email_usuario: false,
    emailUser: false, emailDomain: false, numero_telefono: false, calle: false, num_ext: false, num_int: false,
    colonia: false, estado: false, ciudad: false, c_postal: false
  });
  const [updateLoading, setUpdateLoading] = useState(false);
  const [updateMessage, setUpdateMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [initialFormData, setInitialFormData] = useState({
    primer_nombre: '', segundo_nombre: '', primer_apellido: '', segundo_apellido: '', edad: '', genero: '', tipo_sangre: '',
    num_afiliacion: '', alergias: '', email_usuario: '', emailUser: '', emailDomain: '', numero_telefono: '',
    calle: '', num_ext: '', num_int: '', colonia: '', estado: '', ciudad: '', c_postal: ''
  });

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
      
      const patientData = await response.json();
      console.log('Patient found:', patientData);
      
      // Load patient data into form
      const [emailUser, emailDomain] = patientData.email_usuario.split('@');
      const loadedData = {
        primer_nombre: patientData.primer_nombre || '',
        segundo_nombre: patientData.segundo_nombre || '',
        primer_apellido: patientData.primer_apellido || '',
        segundo_apellido: patientData.segundo_apellido || '',
        edad: patientData.edad?.toString() || '',
        genero: patientData.genero || '',
        tipo_sangre: patientData.tipo_sangre || '',
        num_afiliacion: patientData.num_afiliacion || '',
        alergias: patientData.alergias || '',
        email_usuario: patientData.email_usuario || '',
        emailUser: emailUser || '',
        emailDomain: emailDomain || '',
        numero_telefono: patientData.numero_telefono || '',
        calle: patientData.calle || '',
        num_ext: patientData.num_ext || '',
        num_int: patientData.num_int || '',
        colonia: patientData.colonia || '',
        estado: patientData.estado?.toString() || '',
        ciudad: patientData.ciudad || '',
        c_postal: patientData.c_postal || ''
      };
      
      setFormData(loadedData);
      setInitialFormData(loadedData);
      
      setPatientFound(true);
      
    } catch (error) {
      console.error('Search error:', error);
      setSearchError('Error de conexión. Intente nuevamente.');
      setPatientFound(false);
      // Clear form data on error
      setFormData({
        primer_nombre: '', segundo_nombre: '', primer_apellido: '', segundo_apellido: '', edad: '', genero: '', tipo_sangre: '',
        num_afiliacion: '', alergias: '', email_usuario: '', emailUser: '', emailDomain: '', numero_telefono: '',
        calle: '', num_ext: '', num_int: '', colonia: '', estado: '', ciudad: '', c_postal: ''
      });
    } finally {
      setLoading(false);
    }
  };

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
    }
  };

  const hasFormChanged = () => {
    return JSON.stringify(formData) !== JSON.stringify(initialFormData);
  };

  const handleUpdate = async (event: React.FormEvent) => {
    event.preventDefault();
    setUpdateLoading(true);
    setUpdateMessage(null);
    
    try {
      // Step 1: Update patient in backend
      const response = await fetch(`http://127.0.0.1:8000/api/patients/${numAfiliacion}/update/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al actualizar en la base de datos');
      }

      const updateResult = await response.json();
      console.log('Patient updated:', updateResult);

      // Step 2: Generate XML file for proxy server
      const xmlContent = generatePatientXML(formData, formData.num_afiliacion);
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const fileName = `paciente_${formData.primer_nombre.replace(/\s+/g, '_')}_${formData.num_afiliacion}_${timestamp}.xml`;

      // Step 3: Upload to Google Drive (proxy server)
      if (!isSignedIn) {
        await signIn();
        setIsSignedIn(true);
      }

      await uploadToGoogleDrive(xmlContent, fileName);

      // Update initial form data to reflect successful update
      setInitialFormData(formData);
      
      setUpdateMessage({ type: 'success', text: 'Paciente actualizado exitosamente y enviado al servidor proxy' });
    } catch (error) {
      console.error('Update error:', error);
      setUpdateMessage({ type: 'error', text: error instanceof Error ? error.message : 'Error al actualizar paciente. Intente nuevamente.' });
    } finally {
      setUpdateLoading(false);
    }
  };

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

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={0} sx={{ 
        p: 4, 
        backgroundColor: 'white',
        border: '1px solid #e1e8ed',
        borderRadius: 2
      }}>
        <PatientHeader icon={faUserEdit} title="Actualizar Paciente" />
        
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, mb: 4 }}>
          <TextField
            label="Número de Afiliación"
            value={numAfiliacion}
            onChange={(e) => {
              setNumAfiliacion(e.target.value.replace(/[^0-9]/g, '').slice(0, 8));
              setHasError(false);
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
          <PatientForm
            formData={formData}
            setFormData={setFormData}
            errors={errors}
            setErrors={setErrors}
            onSubmit={handleUpdate}
            loading={updateLoading}
            message={updateMessage}
            buttonText="Actualizar Paciente"
            isUpdate={true}
            isUpdateDisabled={!hasFormChanged()}
            updateTooltip={!hasFormChanged() ? "Ningún cambio se ha realizado a la información del paciente. Compruebe sus cambios." : ""}
          />
        )}
      </Paper>
    </Container>
  );
};

export default PatientUpdate;