import React, { useEffect } from 'react';
import { Box, Typography, Button, Paper, CircularProgress } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  // Automatically log in for development
  useEffect(() => {
    const autoLogin = async () => {
      try {
        // For development, log in automatically
        await login('developer', 'password');
        navigate('/');
      } catch (error) {
        console.error('Auto-login error:', error);
      }
    };
    
    if (!isAuthenticated) {
      autoLogin();
    } else {
      navigate('/');
    }
  }, [isAuthenticated, login, navigate]);
  
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundImage: 'linear-gradient(135deg, #121620 0%, #1E2230 100%)',
        p: 3,
      }}
    >
      <Paper
        sx={{
          width: '100%',
          maxWidth: 400,
          p: 4,
          textAlign: 'center',
          backdropFilter: 'blur(8px)',
          background: 'rgba(30, 34, 48, 0.7)',
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom>
          SparkSQL Agent
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 4 }}>
          Logging in automatically...
        </Typography>
        
        <CircularProgress size={40} sx={{ mb: 3 }} />
        
        <Typography variant="caption" display="block" sx={{ mt: 2 }}>
          You'll be redirected to the dashboard in a moment.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Login; 