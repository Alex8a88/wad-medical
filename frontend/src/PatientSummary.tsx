import React from 'react';
import {
  Typography,
  Box,
  Paper
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser } from '@fortawesome/free-solid-svg-icons';

interface PatientData {
  primer_nombre: string;
  segundo_nombre: string;
  primer_apellido: string;
  segundo_apellido: string;
  edad: string;
  genero: string;
  email_usuario: string;
  alergias: string;
  tipo_sangre: string;
}

interface PatientSummaryProps {
  patientData: PatientData;
}

const PatientSummary: React.FC<PatientSummaryProps> = ({ patientData }) => {
  const getGenderLabel = (genero: string) => {
    switch (genero) {
      case 'M': return 'Masculino';
      case 'F': return 'Femenino';
      case 'X': return 'Otro';
      default: return genero;
    }
  };

  const fullName = `${patientData.primer_nombre} ${patientData.segundo_nombre} ${patientData.primer_apellido} ${patientData.segundo_apellido}`.trim();

  return (
    <Paper elevation={0} sx={{ 
      p: 3, 
      mb: 3,
      backgroundColor: '#f8f9fa',
      border: '1px solid #e1e8ed',
      borderRadius: 2
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <FontAwesomeIcon 
          icon={faUser} 
          style={{ 
            fontSize: '24px', 
            color: '#1976d2', 
            marginRight: '12px' 
          }}
        />
        <Typography variant="h6" sx={{ color: '#1976d2', fontWeight: 'bold' }}>
          Información del Paciente
        </Typography>
      </Box>
      
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        <Box>
          <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
            Nombre Completo
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
            {fullName}
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
            Edad
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
            {patientData.edad} años
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
            Género
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
            {getGenderLabel(patientData.genero)}
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
            Email
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
            {patientData.email_usuario}
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
            Tipo de Sangre
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
            {patientData.tipo_sangre || 'No especificado'}
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
            Alergias
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
            {patientData.alergias || 'Ninguna'}
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default PatientSummary;