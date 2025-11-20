import React from 'react';
import { Box, Typography } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { IconDefinition } from '@fortawesome/free-solid-svg-icons';

interface PatientHeaderProps {
  icon: IconDefinition;
  title: string;
}

const PatientHeader: React.FC<PatientHeaderProps> = ({ icon, title }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 2 }}>
      <FontAwesomeIcon 
        icon={icon} 
        style={{ 
          fontSize: '80px', 
          color: '#1976d2', 
          marginBottom: '16px' 
        }}
      />
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
        {title}
      </Typography>
    </Box>
  );
};

export default PatientHeader;