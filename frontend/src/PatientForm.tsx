import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Stack,
  MenuItem,
  Alert,
  CircularProgress,
  Tooltip
} from '@mui/material';

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

interface PatientFormProps {
  formData: PatientData;
  setFormData: React.Dispatch<React.SetStateAction<PatientData>>;
  errors: FieldErrors;
  setErrors: React.Dispatch<React.SetStateAction<FieldErrors>>;
  onSubmit: (event: React.FormEvent) => void;
  loading: boolean;
  message: {type: 'success' | 'error', text: string} | null;
  buttonText: string;
  isUpdate?: boolean;
  isUpdateDisabled?: boolean;
  updateTooltip?: string;
}

const PatientForm: React.FC<PatientFormProps> = ({
  formData,
  setFormData,
  errors,
  setErrors,
  onSubmit,
  loading,
  message,
  buttonText,
  isUpdate = false,
  isUpdateDisabled = false,
  updateTooltip = ''
}) => {
  const [estados, setEstados] = useState<{id_estado: number, nombre_estado: string}[]>([]);

  const toPascalCase = (str: string) => {
    return str.toLowerCase().split(' ').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const handleChange = (field: keyof PatientData) => (event: React.ChangeEvent<HTMLInputElement>) => {
    let value = event.target.value;
    
    if (field === 'primer_nombre' || field === 'segundo_nombre' || field === 'primer_apellido' || field === 'segundo_apellido') {
      value = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'\-]/g, '');
      value = toPascalCase(value);
    }
    
    if (field === 'emailUser') {
      value = value.replace(/[^a-zA-Z0-9._-]/g, '');
    }
    
    if (field === 'numero_telefono') {
      value = value.replace(/[^0-9]/g, '').slice(0, 10);
    }
    
    const newFormData = { ...formData, [field]: value };
    
    if (field === 'emailUser' || field === 'emailDomain') {
      const user = field === 'emailUser' ? value : formData.emailUser;
      const domain = field === 'emailDomain' ? value : formData.emailDomain;
      newFormData.email_usuario = user && domain ? `${user}@${domain}` : '';
    }
    
    setFormData(newFormData);
    
    if (errors[field]) {
      setErrors({ ...errors, [field]: false });
    }
  };

  const handleBlur = (field: keyof PatientData) => () => {
    const isRequired = field !== 'segundo_apellido' && field !== 'email_usuario';
    const value = formData[field];
    const isEmpty = typeof value === 'string' ? !value.trim() : !value;
    if (isRequired && isEmpty) {
      setErrors({ ...errors, [field]: true });
    }
  };

  useEffect(() => {
    const fetchEstados = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/estados/');
        if (response.ok) {
          const estadosData = await response.json();
          setEstados(estadosData);
        }
      } catch (error) {
        console.error('Error fetching estados:', error);
      }
    };
    
    fetchEstados();
  }, []);

  return (
    <Box component="form" onSubmit={onSubmit} sx={{ mt: 3 }}>
      <Stack spacing={3}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            required
            fullWidth
            label="Nombre"
            value={formData.primer_nombre}
            onChange={handleChange('primer_nombre')}
            onBlur={handleBlur('primer_nombre')}
            variant="outlined"
            inputProps={{ maxLength: 100 }}
            error={errors.primer_nombre}
            helperText={errors.primer_nombre ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.primer_nombre.length}/100`}
          />
          <TextField
            fullWidth
            label="Segundo Nombre"
            value={formData.segundo_nombre}
            onChange={handleChange('segundo_nombre')}
            variant="outlined"
            inputProps={{ maxLength: 100 }}
            helperText={`${formData.segundo_nombre.length}/100`}
          />
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            required
            fullWidth
            label="Primer Apellido"
            value={formData.primer_apellido}
            onChange={handleChange('primer_apellido')}
            onBlur={handleBlur('primer_apellido')}
            variant="outlined"
            inputProps={{ maxLength: 100 }}
            error={errors.primer_apellido}
            helperText={errors.primer_apellido ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.primer_apellido.length}/100`}
          />
          <TextField
            fullWidth
            label="Segundo Apellido"
            value={formData.segundo_apellido}
            onChange={handleChange('segundo_apellido')}
            variant="outlined"
            inputProps={{ maxLength: 100 }}
            helperText={`${formData.segundo_apellido.length}/100`}
          />
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            required
            fullWidth
            label="Edad"
            type="number"
            value={formData.edad}
            onChange={handleChange('edad')}
            onBlur={handleBlur('edad')}
            variant="outlined"
            inputProps={{ min: 0, max: 120 }}
            error={errors.edad}
            helperText={errors.edad ? 'Campo obligatorio. Favor de llenar este campo.' : ''}
          />
          <TextField
            required
            fullWidth
            select
            label="Género"
            value={formData.genero}
            onChange={handleChange('genero')}
            onBlur={handleBlur('genero')}
            variant="outlined"
            error={errors.genero}
            helperText={errors.genero ? 'Campo obligatorio. Favor de llenar este campo.' : ''}
          >
            <MenuItem value="F">Femenino</MenuItem>
            <MenuItem value="M">Masculino</MenuItem>
            <MenuItem value="X">Otro</MenuItem>
          </TextField>
          <TextField
            required
            fullWidth
            select
            label="Tipo de Sangre"
            value={formData.tipo_sangre}
            onChange={handleChange('tipo_sangre')}
            onBlur={handleBlur('tipo_sangre')}
            variant="outlined"
            error={errors.tipo_sangre}
            helperText={errors.tipo_sangre ? 'Campo obligatorio. Favor de llenar este campo.' : ''}
          >
            <MenuItem value="A+">A+</MenuItem>
            <MenuItem value="A-">A-</MenuItem>
            <MenuItem value="B+">B+</MenuItem>
            <MenuItem value="B-">B-</MenuItem>
            <MenuItem value="AB+">AB+</MenuItem>
            <MenuItem value="AB-">AB-</MenuItem>
            <MenuItem value="O+">O+</MenuItem>
            <MenuItem value="O-">O-</MenuItem>
          </TextField>
        </Box>
        
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Alergias"
          value={formData.alergias}
          onChange={handleChange('alergias')}
          variant="outlined"
          helperText="Opcional - Describa cualquier alergia conocida"
        />
        
        <Box>
          <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>Correo Electrónico *</Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
            <TextField
              required
              fullWidth
              label="Usuario"
              value={formData.emailUser}
              onChange={handleChange('emailUser')}
              onBlur={handleBlur('emailUser')}
              variant="outlined"
              inputProps={{ maxLength: 30 }}
              error={errors.emailUser}
              helperText={errors.emailUser ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.emailUser.length}/30`}
            />
            <Typography variant="h6" sx={{ mt: 2 }}>@</Typography>
            <TextField
              required
              fullWidth
              select
              label="Dominio"
              value={formData.emailDomain}
              onChange={handleChange('emailDomain')}
              onBlur={handleBlur('emailDomain')}
              variant="outlined"
              error={errors.emailDomain}
              helperText={errors.emailDomain ? 'Campo obligatorio. Favor de llenar este campo.' : ''}
            >
              <MenuItem value="gmail.com">gmail.com</MenuItem>
              <MenuItem value="outlook.com">outlook.com</MenuItem>
              <MenuItem value="hotmail.com">hotmail.com</MenuItem>
            </TextField>
          </Box>
        </Box>
        
        <TextField
          required
          fullWidth
          label="Teléfono"
          value={formData.numero_telefono}
          onChange={handleChange('numero_telefono')}
          onBlur={handleBlur('numero_telefono')}
          variant="outlined"
          inputProps={{ maxLength: 10 }}
          error={errors.numero_telefono}
          helperText={errors.numero_telefono ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.numero_telefono.length}/10`}
        />
        
        <Box>
          <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>Dirección *</Typography>
          <Stack spacing={2}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                required
                label="Calle"
                value={formData.calle}
                onChange={handleChange('calle')}
                onBlur={handleBlur('calle')}
                variant="outlined"
                inputProps={{ maxLength: 150 }}
                error={errors.calle}
                helperText={errors.calle ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.calle.length}/150`}
                sx={{ flex: 2 }}
              />
              <TextField
                required
                label="Número Exterior"
                value={formData.num_ext}
                onChange={handleChange('num_ext')}
                onBlur={handleBlur('num_ext')}
                variant="outlined"
                inputProps={{ maxLength: 10 }}
                error={errors.num_ext}
                helperText={errors.num_ext ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.num_ext.length}/10`}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Número Interior"
                value={formData.num_int}
                onChange={handleChange('num_int')}
                variant="outlined"
                inputProps={{ maxLength: 10 }}
                helperText={`${formData.num_int.length}/10`}
                sx={{ flex: 1 }}
              />
              <TextField
                required
                label="Colonia"
                value={formData.colonia}
                onChange={handleChange('colonia')}
                onBlur={handleBlur('colonia')}
                variant="outlined"
                inputProps={{ maxLength: 150 }}
                error={errors.colonia}
                helperText={errors.colonia ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.colonia.length}/150`}
                sx={{ flex: 2 }}
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                required
                fullWidth
                select
                label="Estado"
                value={formData.estado}
                onChange={handleChange('estado')}
                onBlur={handleBlur('estado')}
                variant="outlined"
                error={errors.estado}
                helperText={errors.estado ? 'Campo obligatorio. Favor de llenar este campo.' : ''}
              >
                {estados.map((estado) => (
                  <MenuItem key={estado.id_estado} value={estado.id_estado}>
                    {estado.nombre_estado}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                required
                fullWidth
                label="Ciudad"
                value={formData.ciudad}
                onChange={handleChange('ciudad')}
                onBlur={handleBlur('ciudad')}
                variant="outlined"
                inputProps={{ maxLength: 100 }}
                error={errors.ciudad}
                helperText={errors.ciudad ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.ciudad.length}/100`}
              />
              <TextField
                required
                fullWidth
                label="Código Postal"
                value={formData.c_postal}
                onChange={handleChange('c_postal')}
                onBlur={handleBlur('c_postal')}
                variant="outlined"
                inputProps={{ maxLength: 5 }}
                error={errors.c_postal}
                helperText={errors.c_postal ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.c_postal.length}/5`}
              />
            </Box>
          </Stack>
        </Box>
      </Stack>
      
      {message && (
        <Alert severity={message.type} sx={{ mt: 2 }}>
          {message.text}
        </Alert>
      )}
      
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Tooltip title={isUpdate && isUpdateDisabled ? updateTooltip : ''} arrow>
          <span>
            <Button
              type="submit"
              variant="contained"
              size="large"
              sx={{ px: 4, py: 1.5 }}
              disabled={loading || (isUpdate && isUpdateDisabled)}
              startIcon={loading ? <CircularProgress size={20} /> : null}
            >
              {loading ? 'Procesando...' : buttonText}
            </Button>
          </span>
        </Tooltip>
      </Box>
    </Box>
  );
};

export default PatientForm;