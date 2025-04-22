import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Box,
  CircularProgress,
  Alert,
  IconButton,
  Grid
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import axios from '../utils/axiosConfig';

const ConnectionDialog = ({ open, onClose, onConnectionAdded, connectionToEdit }) => {
  const isEditMode = !!connectionToEdit;
  
  const [formData, setFormData] = useState({
    name: connectionToEdit?.name || '',
    type: connectionToEdit?.type || 'postgresql',
    host: connectionToEdit?.host || 'localhost',
    port: connectionToEdit?.port || '5432',
    database: connectionToEdit?.database || '',
    username: connectionToEdit?.username || '',
    password: connectionToEdit?.password || '',
  });
  
  const [testStatus, setTestStatus] = useState({
    loading: false,
    success: false,
    error: null,
  });
  
  const [saveStatus, setSaveStatus] = useState({
    loading: false,
    error: null,
  });
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Reset test status when form changes
    if (testStatus.success || testStatus.error) {
      setTestStatus({
        loading: false,
        success: false,
        error: null,
      });
    }
  };
  
  const handleTestConnection = async () => {
    try {
      setTestStatus({
        loading: true,
        success: false,
        error: null,
      });
      
      const response = await axios.post('/test-connection', formData);
      
      setTestStatus({
        loading: false,
        success: true,
        error: null,
      });
    } catch (err) {
      console.error('Connection test failed:', err);
      
      setTestStatus({
        loading: false,
        success: false,
        error: err.response?.data?.detail || 'Failed to connect to database',
      });
    }
  };
  
  const handleSaveConnection = async () => {
    try {
      setSaveStatus({
        loading: true,
        error: null,
      });
      
      let response;
      if (isEditMode) {
        response = await axios.put(`/connections/${connectionToEdit.id}`, formData);
      } else {
        response = await axios.post('/connections', formData);
      }
      
      setSaveStatus({
        loading: false,
        error: null,
      });
      
      // Call the parent callback with the new connection ID
      onConnectionAdded(response.data.id || connectionToEdit?.id);
    } catch (err) {
      console.error('Failed to save connection:', err);
      
      setSaveStatus({
        loading: false,
        error: err.response?.data?.detail || 'Failed to save connection',
      });
    }
  };

  const validateForm = () => {
    return formData.name && formData.host && formData.port && formData.database;
  };
  
  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">
          {isEditMode ? 'Edit Database Connection' : 'Add Database Connection'}
        </Typography>
        <IconButton edge="end" onClick={onClose} aria-label="close">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      
      <DialogContent dividers>
        <Box component="form" noValidate sx={{ mt: 1 }}>
          <TextField
            margin="normal"
            required
            fullWidth
            label="Connection Name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            autoFocus
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel id="connection-type-label">Database Type</InputLabel>
            <Select
              labelId="connection-type-label"
              name="type"
              value={formData.type}
              onChange={handleChange}
              label="Database Type"
            >
              <MenuItem value="postgresql">PostgreSQL</MenuItem>
              <MenuItem value="mysql">MySQL</MenuItem>
              <MenuItem value="sqlite">SQLite</MenuItem>
              <MenuItem value="oracle">Oracle</MenuItem>
              <MenuItem value="mssql">SQL Server</MenuItem>
            </Select>
          </FormControl>
          
          <Grid container spacing={2}>
            <Grid item xs={8}>
              <TextField
                margin="normal"
                required
                fullWidth
                label="Host"
                name="host"
                value={formData.host}
                onChange={handleChange}
              />
            </Grid>
            <Grid item xs={4}>
              <TextField
                margin="normal"
                required
                fullWidth
                label="Port"
                name="port"
                value={formData.port}
                onChange={handleChange}
              />
            </Grid>
          </Grid>
          
          <TextField
            margin="normal"
            required
            fullWidth
            label="Database Name"
            name="database"
            value={formData.database}
            onChange={handleChange}
          />
          
          <TextField
            margin="normal"
            fullWidth
            label="Username"
            name="username"
            value={formData.username}
            onChange={handleChange}
          />
          
          <TextField
            margin="normal"
            fullWidth
            label="Password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
          />
          
          {/* Test connection status */}
          {(testStatus.success || testStatus.error) && (
            <Box sx={{ mt: 2 }}>
              {testStatus.success && (
                <Alert 
                  severity="success"
                  icon={<CheckCircleIcon />}
                >
                  Connection successful!
                </Alert>
              )}
              
              {testStatus.error && (
                <Alert 
                  severity="error"
                  icon={<ErrorIcon />}
                >
                  {testStatus.error}
                </Alert>
              )}
            </Box>
          )}
          
          {/* Save error message */}
          {saveStatus.error && (
            <Box sx={{ mt: 2 }}>
              <Alert severity="error">{saveStatus.error}</Alert>
            </Box>
          )}
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button 
          onClick={handleTestConnection} 
          color="info" 
          variant="outlined"
          disabled={!validateForm() || testStatus.loading || saveStatus.loading}
          startIcon={testStatus.loading ? <CircularProgress size={20} /> : null}
        >
          Test Connection
        </Button>
        <Box sx={{ flexGrow: 1 }} />
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button 
          onClick={handleSaveConnection} 
          color="primary" 
          variant="contained"
          disabled={!validateForm() || saveStatus.loading}
          startIcon={saveStatus.loading ? <CircularProgress size={20} /> : null}
        >
          {isEditMode ? 'Update' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConnectionDialog; 