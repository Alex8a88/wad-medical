import React, { useState } from 'react';
import {
  Container,
  Button,
  Typography,
  Box,
  Card,
  CardContent,
  Avatar,
  Popover,
  Tabs,
  Tab,
  Menu,
  MenuItem
} from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faUser, faPills, faUserPlus, faUserEdit, faUserMinus, faUserMd, faPrescriptionBottleAlt, faFileMedical, faPaperPlane, faPlusCircle } from '@fortawesome/free-solid-svg-icons';
import Login from './Login';
import Dashboard from './Dashboard';
import PatientRegistration from './PatientRegistration';
import PatientUpdate from './PatientUpdate';
import GenerarReceta from './GenerarReceta';
import AddMedication from './AddMedication';
import DoctorRegistration from './DoctorRegistration';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    background: {
      default: '#ffffff',
    },
  },
});

interface UserInfo {
  user_id: number;
  primer_nombre: string;
  nombre_completo: string;
  email_usuario: string;
  genero: string;
  cedula_profesional?: string;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [userCardAnchor, setUserCardAnchor] = useState<HTMLElement | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [patientsMenuAnchor, setPatientsMenuAnchor] = useState<HTMLElement | null>(null);
  const [doctorsMenuAnchor, setDoctorsMenuAnchor] = useState<HTMLElement | null>(null);
  const [recetasMenuAnchor, setRecetasMenuAnchor] = useState<HTMLElement | null>(null);
  const [farmaciaMenuAnchor, setFarmaciaMenuAnchor] = useState<HTMLElement | null>(null);
  const patientsTabRef = React.useRef<HTMLElement>(null);



  const handleLogin = async (userData?: any) => {
    setIsAuthenticated(true);
    if (userData) {
      setUserInfo(userData);
    } else {
      await fetchUserInfo();
    }
  };

  const fetchUserInfo = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/auth/check/', {
        credentials: 'include',
      });
      const data = await response.json();
      if (data.authenticated) {
        setUserInfo(data);
      }
    } catch (error) {
      console.error('Error fetching user info:', error);
    }
  };

  React.useEffect(() => {
    if (isAuthenticated && !userInfo) {
      fetchUserInfo();
    }
  }, [isAuthenticated]);

  const handleLogout = async () => {
    try {
      await fetch('http://127.0.0.1:8000/api/auth/logout/', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setIsAuthenticated(false);
      setUserInfo(null);
      setUserCardAnchor(null);
    }
  };

  const handleUserCardClick = (event: React.MouseEvent<HTMLElement>) => {
    setUserCardAnchor(event.currentTarget);
  };

  const handleUserCardClose = () => {
    setUserCardAnchor(null);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    if (newValue !== 1 && newValue !== 2 && newValue !== 3 && newValue !== 4) { // Don't change tab for Pacientes, Doctores, Recetas, and Farmacia
      setCurrentTab(newValue);
    }
  };

  const handlePatientsHover = (event: React.MouseEvent<HTMLElement>) => {
    setPatientsMenuAnchor(event.currentTarget);
  };

  const handlePatientsMenuClose = () => {
    setPatientsMenuAnchor(null);
  };

  const handleDoctorsHover = (event: React.MouseEvent<HTMLElement>) => {
    setDoctorsMenuAnchor(event.currentTarget);
  };

  const handleDoctorsMenuClose = () => {
    setDoctorsMenuAnchor(null);
  };

  const handleRecetasHover = (event: React.MouseEvent<HTMLElement>) => {
    setRecetasMenuAnchor(event.currentTarget);
  };

  const handleRecetasMenuClose = () => {
    setRecetasMenuAnchor(null);
  };

  const handleFarmaciaHover = (event: React.MouseEvent<HTMLElement>) => {
    setFarmaciaMenuAnchor(event.currentTarget);
  };

  const handleFarmaciaMenuClose = () => {
    setFarmaciaMenuAnchor(null);
  };

  const handlePatientAction = (action: string) => {
    if (action === 'register') {
      setCurrentTab(1);
    } else if (action === 'update') {
      setCurrentTab(5); // New tab for patient update
    }
    // TODO: Add handlers for suspend
    setPatientsMenuAnchor(null);
  };

  const handleDoctorAction = (action: string) => {
    if (action === 'register') {
      setCurrentTab(2);
    }
    // TODO: Add handlers for update and suspend
    setDoctorsMenuAnchor(null);
  };

  const handleRecetaAction = (action: string) => {
    if (action === 'generar') {
      setCurrentTab(6); // New tab for generar receta
    } else if (action === 'mandar') {
      setCurrentTab(7); // New tab for mandar receta
    }
    setRecetasMenuAnchor(null);
  };

  const handleFarmaciaAction = (action: string) => {
    if (action === 'add') {
      setCurrentTab(8); // New tab for add medication
    }
    setFarmaciaMenuAnchor(null);
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ 
        minHeight: '100vh', 
        display: 'flex', 
        flexDirection: 'column',
        scrollbarGutter: 'stable'
      }}>
        {/* Header */}
        <Box sx={{ 
          position: 'sticky',
          top: 0,
          zIndex: 1100,
          backgroundColor: 'white', 
          color: '#333', 
          borderBottom: '1px solid #e1e8ed'
        }}>
          <Container maxWidth="lg">
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 2 }}>
              <Box 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 2, 
                  cursor: 'pointer',
                  '&:hover': { opacity: 0.8 }
                }}
                onClick={() => setCurrentTab(0)}
              >
                <img src="/Medical logo.png" alt="Medical Logo" style={{ width: '40px', height: '40px' }} />
                <Typography variant="h6" component="h1">Sistema Médico</Typography>
              </Box>
              
              {/* Navigation Tabs in the middle */}
              <Tabs 
                value={currentTab} 
                onChange={handleTabChange}
                sx={{ minHeight: '40px', '& .MuiTab-root': { minHeight: '40px', py: 0.5 } }}
              >
                <Tab 
                  icon={<FontAwesomeIcon icon={faHome} />} 
                  label="Inicio" 
                  iconPosition="start"
                />
                <Tab 
                  icon={<FontAwesomeIcon icon={faUser} />} 
                  label="Pacientes" 
                  iconPosition="start"
                  onMouseEnter={handlePatientsHover}
                />
                <Tab 
                  icon={<FontAwesomeIcon icon={faUserMd} />} 
                  label="Doctores" 
                  iconPosition="start"
                  onMouseEnter={handleDoctorsHover}
                />
                <Tab 
                  icon={<FontAwesomeIcon icon={faPrescriptionBottleAlt} />} 
                  label="Recetas" 
                  iconPosition="start"
                  onMouseEnter={handleRecetasHover}
                />
                <Tab 
                  icon={<FontAwesomeIcon icon={faPills} />} 
                  label="Farmacia" 
                  iconPosition="start"
                  onMouseEnter={handleFarmaciaHover}
                />
              </Tabs>
              
              <Box 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1, 
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  '&:hover': { backgroundColor: 'rgba(0,0,0,0.05)' }
                }}
                onClick={handleUserCardClick}
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: '#1976d2', color: 'white' }}>
                  {userInfo?.primer_nombre?.charAt(0) || 'U'}
                </Avatar>
                <Typography variant="body2">{userInfo?.primer_nombre || 'Usuario'}</Typography>
              </Box>
              
              <Popover
                open={Boolean(userCardAnchor)}
                anchorEl={userCardAnchor}
                onClose={handleUserCardClose}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'right',
                }}
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
              >
                <Card sx={{ minWidth: 200, boxShadow: 'none' }}>
                  <CardContent sx={{ textAlign: 'center', pb: 1 }}>
                    <Avatar sx={{ width: 60, height: 60, mx: 'auto', mb: 1, bgcolor: '#1976d2' }}>
                      {userInfo?.primer_nombre?.charAt(0) || 'U'}
                    </Avatar>
                    <Typography variant="h6" sx={{ mb: 0.5 }}>{userInfo?.nombre_completo || 'Usuario'}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {userInfo?.email_usuario || 'usuario@email.com'}
                    </Typography>
                    {userInfo?.cedula_profesional && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        Cédula: {userInfo.cedula_profesional}
                      </Typography>
                    )}
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {/* Empty space for consistent spacing */}
                    </Typography>
                    <Button 
                      variant="contained" 
                      color="error" 
                      size="small" 
                      onClick={handleLogout}
                      fullWidth
                    >
                      Cerrar Sesión
                    </Button>
                  </CardContent>
                </Card>
              </Popover>
            </Box>

          </Container>
          
          <Menu
            anchorEl={patientsMenuAnchor}
            open={Boolean(patientsMenuAnchor)}
            onClose={handlePatientsMenuClose}
            MenuListProps={{
              onMouseLeave: handlePatientsMenuClose,
            }}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'left',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'left',
            }}
          >
            <MenuItem onClick={() => handlePatientAction('register')}>
              <FontAwesomeIcon icon={faUserPlus} style={{ marginRight: '8px' }} />
              Registrar Paciente
            </MenuItem>
            <MenuItem onClick={() => handlePatientAction('update')}>
              <FontAwesomeIcon icon={faUserEdit} style={{ marginRight: '8px' }} />
              Actualizar Paciente
            </MenuItem>
            <MenuItem onClick={() => handlePatientAction('suspend')}>
              <FontAwesomeIcon icon={faUserMinus} style={{ marginRight: '8px' }} />
              Suspender Paciente
            </MenuItem>
          </Menu>

          <Menu
            anchorEl={doctorsMenuAnchor}
            open={Boolean(doctorsMenuAnchor)}
            onClose={handleDoctorsMenuClose}
            MenuListProps={{
              onMouseLeave: handleDoctorsMenuClose,
            }}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'left',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'left',
            }}
          >
            <MenuItem onClick={() => handleDoctorAction('register')}>
              <FontAwesomeIcon icon={faUserPlus} style={{ marginRight: '8px' }} />
              Registrar Doctor
            </MenuItem>
            <MenuItem onClick={() => handleDoctorAction('update')}>
              <FontAwesomeIcon icon={faUserEdit} style={{ marginRight: '8px' }} />
              Actualizar Doctor
            </MenuItem>
            <MenuItem onClick={() => handleDoctorAction('suspend')}>
              <FontAwesomeIcon icon={faUserMinus} style={{ marginRight: '8px' }} />
              Suspender Doctor
            </MenuItem>
          </Menu>

          <Menu
            anchorEl={recetasMenuAnchor}
            open={Boolean(recetasMenuAnchor)}
            onClose={handleRecetasMenuClose}
            MenuListProps={{
              onMouseLeave: handleRecetasMenuClose,
            }}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'left',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'left',
            }}
          >
            <MenuItem onClick={() => handleRecetaAction('generar')}>
              <FontAwesomeIcon icon={faFileMedical} style={{ marginRight: '8px' }} />
              Generar Receta
            </MenuItem>
            <MenuItem onClick={() => handleRecetaAction('mandar')}>
              <FontAwesomeIcon icon={faPaperPlane} style={{ marginRight: '8px' }} />
              Mandar Receta
            </MenuItem>
          </Menu>

          <Menu
            anchorEl={farmaciaMenuAnchor}
            open={Boolean(farmaciaMenuAnchor)}
            onClose={handleFarmaciaMenuClose}
            MenuListProps={{
              onMouseLeave: handleFarmaciaMenuClose,
            }}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'left',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'left',
            }}
          >
            <MenuItem onClick={() => handleFarmaciaAction('add')}>
              <FontAwesomeIcon icon={faPlusCircle} style={{ marginRight: '8px' }} />
              Añadir Medicamentos
            </MenuItem>
          </Menu>
        </Box>

        {/* Main Content */}
        <Box sx={{ 
          flex: 1, 
          backgroundColor: '#fafbfc'
        }}>
          {currentTab === 0 && <Dashboard userInfo={userInfo} />}
          {currentTab === 1 && <PatientRegistration />}
          {currentTab === 2 && <DoctorRegistration />}
          {currentTab === 3 && (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h4" sx={{ color: '#1976d2' }}>
                Recetas
              </Typography>
              <Typography variant="body1" sx={{ mt: 2, color: '#666' }}>
                Seleccione una opción del menú Recetas
              </Typography>
            </Box>
          )}
          {currentTab === 4 && (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h4" sx={{ color: '#1976d2' }}>
                Farmacia
              </Typography>
              <Typography variant="body1" sx={{ mt: 2, color: '#666' }}>
                Seleccione una opción del menú Farmacia
              </Typography>
            </Box>
          )}
          {currentTab === 5 && <PatientUpdate />}
          {currentTab === 6 && <GenerarReceta />}
          {currentTab === 7 && (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h4" sx={{ color: '#1976d2' }}>
                Mandar Receta
              </Typography>
              <Typography variant="body1" sx={{ mt: 2, color: '#666' }}>
                Módulo en desarrollo
              </Typography>
            </Box>
          )}
          {currentTab === 8 && <AddMedication />}
        </Box>

        {/* Footer */}
        <Box sx={{ 
          backgroundColor: '#f1f3f4', 
          color: '#333', 
          py: 3, 
          mt: 'auto',
          borderTop: '1px solid #e1e8ed'
        }}>
          <Container maxWidth="lg">
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Sistema de Gestión de Pacientes - 2025
              </Typography>
              <Typography variant="caption" sx={{ color: '#666' }}>
                Desarrollado para el manejo seguro de información médica. Todos los derechos reservados. Diseño de Aplicaciones Web.
              </Typography>
            </Box>
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;