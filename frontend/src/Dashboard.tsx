import React, { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';

interface UserInfo {
  user_id: number;
  primer_nombre: string;
  nombre_completo: string;
  email_usuario: string;
  genero: string;
  cedula_profesional?: string;
}

interface DashboardProps {
  userInfo: UserInfo | null;
}

const Dashboard: React.FC<DashboardProps> = ({ userInfo }) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-MX', {
      timeZone: 'America/Mexico_City',
      hour12: true,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('es-MX', {
      timeZone: 'America/Mexico_City',
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getGreeting = () => {
    if (!userInfo) return 'Bienvenid@, Usuario';
    
    const { primer_nombre, genero } = userInfo;
    
    if (genero === 'M') {
      return `Bienvenido, ${primer_nombre}`;
    } else if (genero === 'F') {
      return `Bienvenida, ${primer_nombre}`;
    } else {
      return `Bienvenid@, ${primer_nombre}`;
    }
  };

  return (
    <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}>
      <Box sx={{
        backgroundColor: 'white',
        padding: 4,
        borderRadius: 2,
        border: '1px solid #e1e8ed',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        minWidth: '700px'
      }}>
        {/* Main Dashboard */}
        <Box sx={{
          backgroundColor: 'white',
          padding: 4,
          borderRadius: 2,
          border: '1px solid #e1e8ed',
          display: 'grid',
          gridTemplateColumns: '1fr 1px 1fr',
          gap: 4
        }}>
          {/* Left Column - Clock */}
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" sx={{ mb: 1, color: '#2c3e50', fontWeight: 500 }}>
              {formatTime(currentTime)}
            </Typography>
            <Typography variant="h6" sx={{ color: '#7f8c8d' }}>
              {formatDate(currentTime)}
            </Typography>
            <Typography variant="caption" sx={{ color: '#95a5a6', mt: 1, display: 'block' }}>
              GMT-6 (Hora de México)
            </Typography>
          </Box>
          
          {/* Divider Line */}
          <Box sx={{
            backgroundColor: '#d0d0d0',
            width: '1px',
            alignSelf: 'stretch'
          }} />
          
          {/* Right Column - Greeting */}
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            textAlign: 'center'
          }}>
            <Typography variant="h3" sx={{ color: '#2c3e50', fontWeight: 600 }}>
              {getGreeting()}
            </Typography>
          </Box>
        </Box>

        {/* Notifications Dashboard */}
        <Box sx={{
          backgroundColor: 'white',
          padding: 3,
          borderRadius: 2,
          border: '1px solid #e1e8ed'
        }}>
          <Typography variant="h5" sx={{ mb: 2, color: '#2c3e50', fontWeight: 500 }}>
            Notificaciones
          </Typography>
          <Typography variant="body2" sx={{ color: '#7f8c8d', textAlign: 'center', py: 2 }}>
            No hay notificaciones nuevas
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default Dashboard;