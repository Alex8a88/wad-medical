import React, { useState } from 'react';
import {
  Container,
  Paper,
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
  MenuItem
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPills } from '@fortawesome/free-solid-svg-icons';
import PatientHeader from './PatientHeader';

const AddMedication: React.FC = () => {
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    via_administracion: '',
    formato: ''
  });
  
  const [errors, setErrors] = useState({
    nombre: false,
    descripcion: false,
    via_administracion: false,
    formato: false
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  const viaAdministracionOptions = [
    { value: 'oral', label: 'Oral' },
    { value: 'topica', label: 'Tópica' },
    { value: 'inyectable', label: 'Inyectable' },
    { value: 'gaseosa', label: 'Gaseosa' },
    { value: 'vaginal', label: 'Vaginal' },
    { value: 'rectal', label: 'Rectal' }
  ];

  const formatoOptions = [
    { value: 'solido', label: 'Sólido' },
    { value: 'semisolido', label: 'Semisólido' },
    { value: 'liquido', label: 'Líquido' },
    { value: 'gaseoso', label: 'Gaseoso' }
  ];

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setErrors(prev => ({ ...prev, [field]: false }));
    setMessage(null);
  };

  const validateForm = () => {
    const newErrors = {
      nombre: !formData.nombre.trim(),
      descripcion: false,
      via_administracion: !formData.via_administracion,
      formato: !formData.formato
    };
    
    setErrors(newErrors);
    return !Object.values(newErrors).some(error => error);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) {
      setMessage({ type: 'error', text: 'Por favor complete todos los campos requeridos' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/prescriptions/medicamentos/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.nombre?.[0] || errorData.error || 'Error al agregar medicamento');
      }

      const result = await response.json();
      console.log('Medication added:', result);

      setMessage({ type: 'success', text: 'Medicamento agregado exitosamente' });
      
      // Reset form
      setFormData({
        nombre: '',
        descripcion: '',
        via_administracion: '',
        formato: ''
      });

    } catch (error) {
      console.error('Add medication error:', error);
      setMessage({ 
        type: 'error', 
        text: error instanceof Error ? error.message : 'Error al agregar medicamento. Intente nuevamente.' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={0} sx={{ 
        p: 4, 
        backgroundColor: 'white',
        border: '1px solid #e1e8ed',
        borderRadius: 2
      }}>
        <PatientHeader icon={faPills} title="Añadir Medicamento" />
        
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <TextField
                sx={{ flex: 1, minWidth: '250px' }}
                label="Nombre del Medicamento"
                value={formData.nombre}
                onChange={(e) => handleInputChange('nombre', e.target.value)}
                error={errors.nombre}
                helperText={errors.nombre ? 'Este campo es requerido' : ''}
                required
                variant="outlined"
              />
              
              <TextField
                sx={{ flex: 1, minWidth: '250px' }}
                select
                label="Vía de Administración"
                value={formData.via_administracion}
                onChange={(e) => handleInputChange('via_administracion', e.target.value)}
                error={errors.via_administracion}
                helperText={errors.via_administracion ? 'Este campo es requerido' : ''}
                required
                variant="outlined"
              >
                {viaAdministracionOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            </Box>
            
            <TextField
              sx={{ maxWidth: '400px' }}
              select
              label="Formato"
              value={formData.formato}
              onChange={(e) => handleInputChange('formato', e.target.value)}
              error={errors.formato}
              helperText={errors.formato ? 'Este campo es requerido' : ''}
              required
              variant="outlined"
            >
              {formatoOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            
            <TextField
              fullWidth
              label="Descripción"
              value={formData.descripcion}
              onChange={(e) => handleInputChange('descripcion', e.target.value)}
              multiline
              rows={3}
              variant="outlined"
              helperText="Descripción opcional del medicamento"
            />
          </Box>

          {message && (
            <Alert severity={message.type} sx={{ mt: 3 }}>
              {message.text}
            </Alert>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={16} /> : <FontAwesomeIcon icon={faPills} />}
              sx={{ px: 4, py: 1.5 }}
            >
              {loading ? 'Agregando...' : 'Agregar Medicamento'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default AddMedication;