import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
  MenuItem,
  Typography,
  Stack
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserPlus } from '@fortawesome/free-solid-svg-icons';

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

interface DoctorFormProps {
  formData: DoctorData;
  setFormData: React.Dispatch<React.SetStateAction<DoctorData>>;
  errors: FieldErrors;
  setErrors: React.Dispatch<React.SetStateAction<FieldErrors>>;
  onSubmit: (event: React.FormEvent) => void;
  loading: boolean;
  message: {type: 'success' | 'error', text: string} | null;
  buttonText: string;
}

interface Estado {
  id_estado: number;
  nombre_estado: string;
}

const DoctorForm: React.FC<DoctorFormProps> = ({
  formData,
  setFormData,
  errors,
  setErrors,
  onSubmit,
  loading,
  message,
  buttonText
}) => {
  const [estados, setEstados] = useState<Estado[]>([]);

  const toPascalCase = (str: string) => {
    return str.toLowerCase().split(' ').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  useEffect(() => {
    const fetchEstados = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/estados/');
        if (response.ok) {
          const data = await response.json();
          setEstados(data);
        }
      } catch (error) {
        console.error('Error fetching estados:', error);
      }
    };

    fetchEstados();
  }, []);

  const handleInputChange = (field: keyof DoctorData, value: string) => {
    // Name validation - allow letters, spaces, accents, apostrophes, hyphens
    if (['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido'].includes(field)) {
      value = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'\-]/g, '');
      value = toPascalCase(value);
    }

    // Age validation - only numbers
    if (field === 'edad') {
      if (!/^\d*$/.test(value)) return;
      if (parseInt(value) > 120) return;
    }

    // Phone validation - only numbers, max 10 digits
    if (field === 'numero_telefono') {
      value = value.replace(/[^0-9]/g, '').slice(0, 10);
    }

    // Postal code validation - only numbers, max 5 digits
    if (field === 'c_postal') {
      value = value.replace(/[^0-9]/g, '').slice(0, 5);
    }

    // Professional license validation - alphanumeric
    if (field === 'cedula_profesional') {
      value = value.replace(/[^a-zA-Z0-9]/g, '');
    }

    // Email user validation
    if (field === 'emailUser') {
      value = value.replace(/[^a-zA-Z0-9._-]/g, '');
    }

    // Email handling
    if (field === 'emailUser' || field === 'emailDomain') {
      const newFormData = { ...formData, [field]: value };
      const user = field === 'emailUser' ? value : formData.emailUser;
      const domain = field === 'emailDomain' ? value : formData.emailDomain;
      newFormData.email_usuario = user && domain ? `${user}@${domain}` : '';
      setFormData(newFormData);
    } else {
      setFormData({ ...formData, [field]: value });
    }

    if (errors[field]) {
      setErrors({ ...errors, [field]: false });
    }
  };

  const handleBlur = (field: keyof DoctorData) => () => {
    const isRequired = !['segundo_nombre', 'segundo_apellido', 'num_int', 'especialidad'].includes(field);
    const value = formData[field];
    const isEmpty = typeof value === 'string' ? !value.trim() : !value;
    if (isRequired && isEmpty) {
      setErrors({ ...errors, [field]: true });
    }
  };

  return (
    <Box component="form" onSubmit={onSubmit} sx={{ mt: 3 }}>
      <Stack spacing={3}>
        {/* Personal Information */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            required
            fullWidth
            label="Nombre"
            value={formData.primer_nombre}
            onChange={(e) => handleInputChange('primer_nombre', e.target.value)}
            onBlur={handleBlur('primer_nombre')}
            error={errors.primer_nombre}
            helperText={errors.primer_nombre ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.primer_nombre.length}/100`}
            inputProps={{ maxLength: 100 }}
          />
          <TextField
            fullWidth
            label="Segundo Nombre"
            value={formData.segundo_nombre}
            onChange={(e) => handleInputChange('segundo_nombre', e.target.value)}
            helperText={`${formData.segundo_nombre.length}/100`}
            inputProps={{ maxLength: 100 }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            required
            fullWidth
            label="Primer Apellido"
            value={formData.primer_apellido}
            onChange={(e) => handleInputChange('primer_apellido', e.target.value)}
            onBlur={handleBlur('primer_apellido')}
            error={errors.primer_apellido}
            helperText={errors.primer_apellido ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.primer_apellido.length}/100`}
            inputProps={{ maxLength: 100 }}
          />
          <TextField
            fullWidth
            label="Segundo Apellido"
            value={formData.segundo_apellido}
            onChange={(e) => handleInputChange('segundo_apellido', e.target.value)}
            helperText={`${formData.segundo_apellido.length}/100`}
            inputProps={{ maxLength: 100 }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            required
            fullWidth
            label="Edad"
            type="number"
            value={formData.edad}
            onChange={(e) => handleInputChange('edad', e.target.value)}
            onBlur={handleBlur('edad')}
            error={errors.edad}
            helperText={errors.edad ? 'Campo obligatorio. Favor de llenar este campo.' : ''}
            inputProps={{ min: 0, max: 120 }}
          />
          <TextField
            required
            fullWidth
            select
            label="Género"
            value={formData.genero}
            onChange={(e) => handleInputChange('genero', e.target.value)}
            onBlur={handleBlur('genero')}
            error={errors.genero}
            helperText={errors.genero ? 'Campo obligatorio. Favor de llenar este campo.' : ''}
          >
            <MenuItem value="F">Femenino</MenuItem>
            <MenuItem value="M">Masculino</MenuItem>
            <MenuItem value="X">Otro</MenuItem>
          </TextField>
        </Box>

        {/* Professional Information */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            required
            fullWidth
            label="Cédula Profesional"
            value={formData.cedula_profesional}
            onChange={(e) => handleInputChange('cedula_profesional', e.target.value)}
            onBlur={handleBlur('cedula_profesional')}
            error={errors.cedula_profesional}
            helperText={errors.cedula_profesional ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.cedula_profesional.length}/20`}
            inputProps={{ maxLength: 20 }}
          />
          <TextField
            fullWidth
            label="Especialidad"
            value={formData.especialidad}
            onChange={(e) => handleInputChange('especialidad', e.target.value)}
            helperText={`${formData.especialidad.length}/100`}
            inputProps={{ maxLength: 100 }}
          />
        </Box>

        {/* Login Information */}
        <Box>
          <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>Información de Acceso *</Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
            <TextField
              required
              fullWidth
              label="Usuario"
              value={formData.emailUser}
              onChange={(e) => handleInputChange('emailUser', e.target.value)}
              onBlur={handleBlur('emailUser')}
              error={errors.emailUser}
              helperText={errors.emailUser ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.emailUser.length}/30`}
              inputProps={{ maxLength: 30 }}
            />
            <Typography variant="h6" sx={{ mt: 2 }}>@</Typography>
            <TextField
              required
              fullWidth
              select
              label="Dominio"
              value={formData.emailDomain}
              onChange={(e) => handleInputChange('emailDomain', e.target.value)}
              onBlur={handleBlur('emailDomain')}
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
          type="password"
          label="Contraseña"
          value={formData.password}
          onChange={(e) => handleInputChange('password', e.target.value)}
          onBlur={handleBlur('password')}
          error={errors.password}
          helperText={errors.password ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.password.length}/50`}
          inputProps={{ maxLength: 50 }}
        />

        <TextField
          required
          fullWidth
          label="Teléfono"
          value={formData.numero_telefono}
          onChange={(e) => handleInputChange('numero_telefono', e.target.value)}
          onBlur={handleBlur('numero_telefono')}
          error={errors.numero_telefono}
          helperText={errors.numero_telefono ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.numero_telefono.length}/10`}
          inputProps={{ maxLength: 10 }}
        />

        {/* Address Information */}
        <Box>
          <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>Dirección *</Typography>
          <Stack spacing={2}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                required
                label="Calle"
                value={formData.calle}
                onChange={(e) => handleInputChange('calle', e.target.value)}
                onBlur={handleBlur('calle')}
                error={errors.calle}
                helperText={errors.calle ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.calle.length}/150`}
                inputProps={{ maxLength: 150 }}
                sx={{ flex: 2 }}
              />
              <TextField
                required
                label="Número Exterior"
                value={formData.num_ext}
                onChange={(e) => handleInputChange('num_ext', e.target.value)}
                onBlur={handleBlur('num_ext')}
                error={errors.num_ext}
                helperText={errors.num_ext ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.num_ext.length}/10`}
                inputProps={{ maxLength: 10 }}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Número Interior"
                value={formData.num_int}
                onChange={(e) => handleInputChange('num_int', e.target.value)}
                helperText={`${formData.num_int.length}/10`}
                inputProps={{ maxLength: 10 }}
                sx={{ flex: 1 }}
              />
              <TextField
                required
                label="Colonia"
                value={formData.colonia}
                onChange={(e) => handleInputChange('colonia', e.target.value)}
                onBlur={handleBlur('colonia')}
                error={errors.colonia}
                helperText={errors.colonia ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.colonia.length}/150`}
                inputProps={{ maxLength: 150 }}
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
                onChange={(e) => handleInputChange('estado', e.target.value)}
                onBlur={handleBlur('estado')}
                error={errors.estado}
                helperText={errors.estado ? 'Campo obligatorio. Favor de llenar este campo.' : ''}
              >
                {estados.map((estado) => (
                  <MenuItem key={estado.id_estado} value={estado.id_estado.toString()}>
                    {estado.nombre_estado}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                required
                fullWidth
                label="Ciudad"
                value={formData.ciudad}
                onChange={(e) => handleInputChange('ciudad', e.target.value)}
                onBlur={handleBlur('ciudad')}
                error={errors.ciudad}
                helperText={errors.ciudad ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.ciudad.length}/100`}
                inputProps={{ maxLength: 100 }}
              />
              <TextField
                required
                fullWidth
                label="Código Postal"
                value={formData.c_postal}
                onChange={(e) => handleInputChange('c_postal', e.target.value)}
                onBlur={handleBlur('c_postal')}
                error={errors.c_postal}
                helperText={errors.c_postal ? 'Campo obligatorio. Favor de llenar este campo.' : `${formData.c_postal.length}/5`}
                inputProps={{ maxLength: 5 }}
              />
            </Box>
          </Stack>
        </Box>
      </Stack>

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
          startIcon={loading ? <CircularProgress size={16} /> : <FontAwesomeIcon icon={faUserPlus} />}
          sx={{ px: 4, py: 1.5 }}
        >
          {loading ? 'Registrando...' : buttonText}
        </Button>
      </Box>
    </Box>
  );
};

export default DoctorForm;