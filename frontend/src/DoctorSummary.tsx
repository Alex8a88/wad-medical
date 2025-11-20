import React from 'react';
import {
  Box,
  Typography,
  Paper
} from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserMd } from '@fortawesome/free-solid-svg-icons';

interface DoctorData {
  id: number;
  nombre: string;
  primer_apellido: string;
  segundo_apellido: string;
  cedula_profesional: string;
  especialidad: string;
}

interface DoctorSummaryProps {
  doctorData: DoctorData;
}

const DoctorSummary: React.FC<DoctorSummaryProps> = ({ doctorData }) => {
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
          icon={faUserMd} 
          style={{ 
            fontSize: '24px', 
            color: '#1976d2', 
            marginRight: '12px' 
          }}
        />
        <Typography variant="h6" sx={{ color: '#1976d2', fontWeight: 'bold' }}>
          Información del Doctor
        </Typography>
      </Box>
      
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        <Box>
          <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
            Nombre Completo
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
            Dr. {doctorData.nombre} {doctorData.primer_apellido} {doctorData.segundo_apellido}
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
            Cédula Profesional
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
            {doctorData.cedula_profesional}
          </Typography>
        </Box>
        
        {doctorData.especialidad && (
          <Box>
            <Typography variant="body2" sx={{ color: '#666', fontWeight: 500 }}>
              Especialidad
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {doctorData.especialidad}
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default DoctorSummary;