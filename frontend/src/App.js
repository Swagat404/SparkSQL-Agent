import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import ConnectionManager from './components/ConnectionManager';
import QueryInterface from './components/QueryInterface';
import ErrorAnalytics from './components/ErrorAnalytics';
import NotFound from './components/NotFound';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import './styles/globals.css';

// Create a theme with dark mode and futuristic design
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#18DCFF',  // Vibrant cyan
      light: '#70E4FF',
      dark: '#0095AB',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#9D4EDD',  // Violet accent
      light: '#B57BEB',
      dark: '#7B2CBF',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#121620',  // Rich dark blue-gray
      paper: '#1E2230',    // Lighter blue-gray
    },
    success: {
      main: '#3BCBB0',     // Soft teal
    },
    error: {
      main: '#FF5A5A',     // Coral red
    },
    warning: {
      main: '#FFC857',     // Amber
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#E2E8F0',
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      'system-ui',
      '-apple-system',
      'BlinkMacSystemFont',
      'Segoe UI',
      'Roboto',
      'Helvetica Neue',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontFamily: '"Space Grotesk", sans-serif',
      fontWeight: 700,
    },
    h2: {
      fontFamily: '"Space Grotesk", sans-serif',
      fontWeight: 700,
    },
    h3: {
      fontFamily: '"Space Grotesk", sans-serif',
      fontWeight: 600,
    },
    h4: {
      fontFamily: '"Space Grotesk", sans-serif',
      fontWeight: 600,
    },
    h5: {
      fontFamily: '"Space Grotesk", sans-serif',
      fontWeight: 500,
    },
    h6: {
      fontFamily: '"Space Grotesk", sans-serif',
      fontWeight: 500,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
    code: {
      fontFamily: '"JetBrains Mono", monospace',
    }
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 24,
          padding: '8px 24px',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 6px 20px rgba(24, 220, 255, 0.3)',
          },
        },
        containedPrimary: {
          background: 'linear-gradient(90deg, #18DCFF 0%, #9D4EDD 150%)',
          '&:hover': {
            background: 'linear-gradient(90deg, #18DCFF 0%, #9D4EDD 120%)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            transition: 'all 0.3s ease',
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: '#18DCFF',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: '#18DCFF',
              boxShadow: '0 0 8px rgba(24, 220, 255, 0.3)',
            },
          },
        },
      },
    },
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          scrollbarColor: '#1E2230 #121620',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#121620',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#1E2230',
            borderRadius: '4px',
            '&:hover': {
              background: '#2A304A',
            },
          },
        },
      },
    },
  },
});

// Protected route component to redirect unauthenticated users
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/connections" element={
              <ProtectedRoute>
                <ConnectionManager />
              </ProtectedRoute>
            } />
            <Route path="/query" element={
              <ProtectedRoute>
                <QueryInterface />
              </ProtectedRoute>
            } />
            <Route path="/analytics" element={
              <ProtectedRoute>
                <ErrorAnalytics />
              </ProtectedRoute>
            } />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App; 