import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Stack,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  MenuItem
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faTrash } from '@fortawesome/free-solid-svg-icons';

interface Medicamento {
  medicamento: string;
  dosis: string;
  frecuencia: string;
}

interface PrescripcionData {
  diagnostico: string;
  medicamentos: Medicamento[];
}

interface PrescripcionFormProps {
  onSubmit: (data: PrescripcionData) => void;
  loading: boolean;
  message: {type: 'success' | 'error', text: string} | null;
  disabled?: boolean;
}

const PrescripcionForm: React.FC<PrescripcionFormProps> = ({
  onSubmit,
  loading,
  message,
  disabled = false
}) => {
  const [formData, setFormData] = useState<PrescripcionData>({
    diagnostico: '',
    medicamentos: [{ medicamento: '', dosis: '', frecuencia: '' }]
  });
  const [errors, setErrors] = useState({
    diagnostico: false,
    medicamentos: [{ medicamento: false, dosis: false, frecuencia: false }]
  });
  const [medicamentosDisponibles, setMedicamentosDisponibles] = useState<any[]>([]);

  useEffect(() => {
    const fetchMedicamentos = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/prescriptions/medicamentos/');
        if (response.ok) {
          const data = await response.json();
          setMedicamentosDisponibles(data);
        }
      } catch (error) {
        console.error('Error fetching medicamentos:', error);
      }
    };
    fetchMedicamentos();
  }, []);

  const handleDiagnosticoChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, diagnostico: event.target.value });
    if (errors.diagnostico) {
      setErrors({ ...errors, diagnostico: false });
    }
  };

  const handleMedicamentoChange = (index: number, field: keyof Medicamento) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const newMedicamentos = [...formData.medicamentos];
    newMedicamentos[index] = { ...newMedicamentos[index], [field]: event.target.value };
    setFormData({ ...formData, medicamentos: newMedicamentos });

    const newErrors = [...errors.medicamentos];
    newErrors[index] = { ...newErrors[index], [field]: false };
    setErrors({ ...errors, medicamentos: newErrors });
  };

  const addMedicamento = () => {
    setFormData({
      ...formData,
      medicamentos: [...formData.medicamentos, { medicamento: '', dosis: '', frecuencia: '' }]
    });
    setErrors({
      ...errors,
      medicamentos: [...errors.medicamentos, { medicamento: false, dosis: false, frecuencia: false }]
    });
  };

  const removeMedicamento = (index: number) => {
    if (formData.medicamentos.length > 1) {
      const newMedicamentos = formData.medicamentos.filter((_, i) => i !== index);
      const newErrors = errors.medicamentos.filter((_, i) => i !== index);
      setFormData({ ...formData, medicamentos: newMedicamentos });
      setErrors({ ...errors, medicamentos: newErrors });
    }
  };

  const validateForm = () => {
    let hasErrors = false;
    const newErrors = {
      diagnostico: !formData.diagnostico.trim(),
      medicamentos: formData.medicamentos.map(med => ({
        medicamento: !med.medicamento.trim(),
        dosis: !med.dosis.trim(),
        frecuencia: !med.frecuencia.trim()
      }))
    };

    if (newErrors.diagnostico) hasErrors = true;
    newErrors.medicamentos.forEach(medError => {
      if (medError.medicamento || medError.dosis || medError.frecuencia) hasErrors = true;
    });

    setErrors(newErrors);
    return !hasErrors;
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
      <Stack spacing={3}>
        <TextField
          required
          fullWidth
          label="Diagnóstico"
          value={formData.diagnostico}
          onChange={handleDiagnosticoChange}
          variant="outlined"
          multiline
          rows={2}
          inputProps={{ maxLength: 500 }}
          error={errors.diagnostico}
          helperText={errors.diagnostico ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.diagnostico.length}/500`}
        />

        <Box>
          <Typography variant="h6" sx={{ mb: 2, color: '#1976d2' }}>
            Medicamentos
          </Typography>
          
          {formData.medicamentos.map((medicamento, index) => (
            <Box key={index} sx={{ mb: 2, p: 2, border: '1px solid #e1e8ed', borderRadius: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  Medicamento {index + 1}
                </Typography>
                {formData.medicamentos.length > 1 && (
                  <Tooltip title="Quitar medicamento">
                    <IconButton 
                      onClick={() => removeMedicamento(index)}
                      size="small"
                      color="error"
                    >
                      <FontAwesomeIcon icon={faTrash} />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
              
              <Stack spacing={2}>
                <TextField
                  select
                  required
                  fullWidth
                  label="Medicamento"
                  value={medicamento.medicamento}
                  onChange={handleMedicamentoChange(index, 'medicamento')}
                  variant="outlined"
                  error={errors.medicamentos[index]?.medicamento}
                  helperText={errors.medicamentos[index]?.medicamento ? 'Campo obligatorio. Favor de llenar este campo.' : ''}
                >
                  {medicamentosDisponibles.map((med) => (
                    <MenuItem key={med.id} value={med.nombre}>
                      {med.nombre}
                    </MenuItem>
                  ))}
                </TextField>
                
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <TextField
                    required
                    fullWidth
                    label="Dosis"
                    value={medicamento.dosis}
                    onChange={handleMedicamentoChange(index, 'dosis')}
                    variant="outlined"
                    inputProps={{ maxLength: 100 }}
                    error={errors.medicamentos[index]?.dosis}
                    helperText={errors.medicamentos[index]?.dosis ? 'Campo obligatorio. Favor de llenar este campo.' : `${medicamento.dosis.length}/100`}
                    placeholder="e.g. 500mg, 1 tableta"
                  />
                  
                  <TextField
                    required
                    fullWidth
                    label="Frecuencia"
                    value={medicamento.frecuencia}
                    onChange={handleMedicamentoChange(index, 'frecuencia')}
                    variant="outlined"
                    inputProps={{ maxLength: 100 }}
                    error={errors.medicamentos[index]?.frecuencia}
                    helperText={errors.medicamentos[index]?.frecuencia ? 'Campo obligatorio. Favor de llenar este campo.' : `${medicamento.frecuencia.length}/100`}
                    placeholder="e.g. cada 8 horas, 2 veces al día"
                  />
                </Box>
              </Stack>
            </Box>
          ))}
          
          <Button
            variant="outlined"
            startIcon={<FontAwesomeIcon icon={faPlus} />}
            onClick={addMedicamento}
            sx={{ mt: 1 }}
          >
            Agregar Medicamento
          </Button>
        </Box>
      </Stack>
      
      {message && (
        <Alert severity={message.type} sx={{ mt: 2 }}>
          {message.text}
        </Alert>
      )}
      
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Button
          type="submit"
          variant="contained"
          size="large"
          sx={{ px: 4, py: 1.5 }}
          disabled={loading || disabled}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Generando...' : disabled ? 'Receta Generada' : 'Generar Receta'}
        </Button>
      </Box>
    </Box>
  );
};

export default PrescripcionForm;