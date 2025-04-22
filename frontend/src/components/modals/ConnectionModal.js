import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  CircularProgress,
  Tabs,
  Tab,
  Alert,
  Switch,
  FormControlLabel,
  Tooltip
} from '@mui/material';
import { styled } from '@mui/material/styles';
import CloseIcon from '@mui/icons-material/Close';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import GlassCard from '../ui/GlassCard';

// Styled tab for custom appearance
const StyledTab = styled(Tab)(({ theme }) => ({
  minHeight: '40px',
  fontSize: '0.875rem',
  padding: '0 16px',
  '&.Mui-selected': {
    color: theme.palette.primary.main,
  },
}));

/**
 * ConnectionModal Component
 * A modal for setting up and testing database connections
 * 
 * @param {Object} props
 * @param {boolean} props.open - Whether the modal is open
 * @param {function} props.onClose - Callback for closing the modal
 * @param {function} props.onSave - Callback for saving a connection
 * @param {Object} [props.initialValues] - Initial values for editing an existing connection
 */
const ConnectionModal = ({
  open,
  onClose,
  onSave,
  initialValues = null
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [connectionString, setConnectionString] = useState('');
  const [showConnectionString, setShowConnectionString] = useState(false);
  const [testStatus, setTestStatus] = useState(null); // null, 'loading', 'success', 'error'
  const [copied, setCopied] = useState(false);
  
  // Form state
  const [formValues, setFormValues] = useState({
    name: initialValues?.name || '',
    type: initialValues?.type || 'postgresql',
    host: initialValues?.host || 'localhost',
    port: initialValues?.port || (initialValues?.type === 'mysql' ? '3306' : '5432'),
    database: initialValues?.database || '',
    username: initialValues?.username || '',
    password: initialValues?.password || '',
  });
  
  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Update port based on database type
    if (name === 'type') {
      setFormValues({
        ...formValues,
        [name]: value,
        port: value === 'mysql' ? '3306' : '5432'
      });
    } else {
      setFormValues({
        ...formValues,
        [name]: value
      });
    }
  };
  
  // Generate connection string based on form values
  React.useEffect(() => {
    let connString = '';
    
    if (formValues.type === 'postgresql') {
      connString = `postgresql://${formValues.username}:${showConnectionString ? formValues.password : '********'}@${formValues.host}:${formValues.port}/${formValues.database}`;
    } else if (formValues.type === 'mysql') {
      connString = `mysql://${formValues.username}:${showConnectionString ? formValues.password : '********'}@${formValues.host}:${formValues.port}/${formValues.database}`;
    }
    
    setConnectionString(connString);
  }, [formValues, showConnectionString]);
  
  // Handle connection test
  const handleTestConnection = async () => {
    setTestStatus('loading');
    
    // Simulate API call
    setTimeout(() => {
      // Random success/failure for demo
      const success = Math.random() > 0.3;
      setTestStatus(success ? 'success' : 'error');
    }, 1500);
  };
  
  // Handle copy connection string
  const handleCopyConnectionString = () => {
    navigator.clipboard.writeText(connectionString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  // Handle save connection
  const handleSave = () => {
    onSave({
      ...formValues,
      id: initialValues?.id
    });
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          backgroundColor: 'background.paper',
          backgroundImage: 'none',
          borderRadius: 2,
          overflow: 'hidden',
        }
      }}
    >
      {/* Header */}
      <DialogTitle sx={{ 
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Typography variant="h6" fontFamily="'Space Grotesk', sans-serif">
          {initialValues ? 'Edit Connection' : 'New Database Connection'}
        </Typography>
        <IconButton onClick={onClose}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      
      {/* Connection Mode Tabs */}
      <Box sx={{ 
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
      }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ 
            '& .MuiTabs-indicator': {
              background: 'linear-gradient(90deg, #18DCFF 0%, #9D4EDD 100%)',
              height: 3,
            }
          }}
        >
          <StyledTab label="Connection Form" />
          <StyledTab label="Connection String" />
        </Tabs>
      </Box>
      
      <DialogContent sx={{ p: 3 }}>
        {/* Connection Form */}
        <Box hidden={activeTab !== 0}>
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <TextField
              fullWidth
              label="Connection Name"
              name="name"
              value={formValues.name}
              onChange={handleInputChange}
              placeholder="My Database"
              required
            />
            
            <FormControl fullWidth>
              <InputLabel>Database Type</InputLabel>
              <Select
                name="type"
                value={formValues.type}
                onChange={handleInputChange}
                label="Database Type"
              >
                <MenuItem value="postgresql">PostgreSQL</MenuItem>
                <MenuItem value="mysql">MySQL</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <GlassCard intensity="light" sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                fullWidth
                label="Host"
                name="host"
                value={formValues.host}
                onChange={handleInputChange}
                placeholder="localhost"
                required
              />
              
              <TextField
                label="Port"
                name="port"
                value={formValues.port}
                onChange={handleInputChange}
                sx={{ width: '30%' }}
                required
              />
            </Box>
            
            <TextField
              fullWidth
              label="Database Name"
              name="database"
              value={formValues.database}
              onChange={handleInputChange}
              placeholder={formValues.type === 'postgresql' ? 'postgres' : 'mysql'}
              sx={{ mb: 2 }}
              required
            />
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                label="Username"
                name="username"
                value={formValues.username}
                onChange={handleInputChange}
                placeholder={formValues.type === 'postgresql' ? 'postgres' : 'root'}
                required
              />
              
              <TextField
                fullWidth
                label="Password"
                name="password"
                value={formValues.password}
                onChange={handleInputChange}
                type={showConnectionString ? 'text' : 'password'}
                required
              />
            </Box>
          </GlassCard>
          
          <FormControlLabel
            control={
              <Switch 
                checked={showConnectionString} 
                onChange={() => setShowConnectionString(!showConnectionString)} 
              />
            }
            label="Show passwords"
          />
        </Box>
        
        {/* Connection String */}
        <Box hidden={activeTab !== 1} sx={{ height: '100%' }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Create a connection using a database connection string.
          </Typography>
          
          <GlassCard intensity="light" sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                fullWidth
                label="Connection Name"
                name="name"
                value={formValues.name}
                onChange={handleInputChange}
                placeholder="My Database"
                required
              />
              
              <FormControl sx={{ width: '30%' }}>
                <InputLabel>Database Type</InputLabel>
                <Select
                  name="type"
                  value={formValues.type}
                  onChange={handleInputChange}
                  label="Database Type"
                >
                  <MenuItem value="postgresql">PostgreSQL</MenuItem>
                  <MenuItem value="mysql">MySQL</MenuItem>
                </Select>
              </FormControl>
            </Box>
            
            <Box sx={{ position: 'relative' }}>
              <TextField
                fullWidth
                label="Connection String"
                value={connectionString}
                InputProps={{
                  readOnly: true,
                }}
                multiline
                maxRows={2}
              />
              <Tooltip title={copied ? 'Copied!' : 'Copy connection string'}>
                <IconButton 
                  size="small" 
                  onClick={handleCopyConnectionString}
                  sx={{ 
                    position: 'absolute',
                    right: 8,
                    top: 8,
                  }}
                >
                  {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
            </Box>
          </GlassCard>
        </Box>
        
        {/* Connection Test Result */}
        {testStatus && (
          <Box sx={{ mt: 2 }}>
            {testStatus === 'loading' ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={20} />
                <Typography variant="body2">Testing connection...</Typography>
              </Box>
            ) : testStatus === 'success' ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                Connection successful! Database is accessible.
              </Alert>
            ) : (
              <Alert severity="error" sx={{ mb: 2 }}>
                Connection failed. Please check your credentials and try again.
              </Alert>
            )}
          </Box>
        )}
      </DialogContent>
      
      <DialogActions sx={{ 
        p: 2,
        borderTop: '1px solid rgba(255, 255, 255, 0.05)'
      }}>
        <Button 
          onClick={handleTestConnection} 
          variant="outlined"
          disabled={testStatus === 'loading' || !formValues.host || !formValues.database}
          startIcon={testStatus === 'loading' ? <CircularProgress size={16} /> : null}
        >
          Test Connection
        </Button>
        <Button 
          onClick={handleSave} 
          variant="contained"
          disabled={
            !formValues.name || 
            !formValues.host || 
            !formValues.port || 
            !formValues.database || 
            !formValues.username || 
            !formValues.password
          }
        >
          Save Connection
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConnectionModal; 