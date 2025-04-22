import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import { styled } from '@mui/material/styles';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { Link as RouterLink } from 'react-router-dom';
import axios from '../utils/axiosConfig';
import ConnectionDialog from './ConnectionDialog';

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  borderBottom: `1px solid ${theme.palette.divider}`,
  padding: theme.spacing(1.5),
  '&.header': {
    backgroundColor: theme.palette.grey[900],
    color: theme.palette.common.white,
    fontWeight: 600,
  }
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  '&:nth-of-type(odd)': {
    backgroundColor: theme.palette.action.hover,
  },
  '&:hover': {
    backgroundColor: theme.palette.action.selected,
  }
}));

const ConnectionManager = () => {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [editConnection, setEditConnection] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    fetchConnections();
  }, [refreshTrigger]);

  const fetchConnections = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log("Fetching connections for manager...");
      
      const response = await axios.get('/connections');
      console.log("Connections response in manager:", response.data);
      
      if (response.data && Object.keys(response.data).length > 0) {
        const connectionsArray = Object.entries(response.data).map(([id, conn]) => ({
          id,
          name: conn.name,
          type: conn.type,
          host: conn.host,
          port: conn.port,
          database: conn.database,
          username: conn.username
        }));
        
        setConnections(connectionsArray);
      } else {
        setConnections([]);
      }
    } catch (err) {
      console.error('Error fetching connections:', err);
      setError('Failed to load connections. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAddDialog = () => {
    setEditConnection(null);
    setIsAddDialogOpen(true);
  };

  const handleOpenEditDialog = (connection) => {
    setEditConnection(connection);
    setIsAddDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setIsAddDialogOpen(false);
    setEditConnection(null);
  };

  const handleConnectionSaved = () => {
    // Trigger a refresh
    setRefreshTrigger(prev => prev + 1);
    handleCloseDialog();
  };

  const handleDeleteConnection = async (connectionId) => {
    if (!window.confirm('Are you sure you want to delete this connection?')) {
      return;
    }

    try {
      setLoading(true);
      await axios.delete(`/connections/${connectionId}`);
      
      // Remove from local state
      setConnections(prev => prev.filter(conn => conn.id !== connectionId));
    } catch (err) {
      console.error('Error deleting connection:', err);
      setError('Failed to delete connection. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: '1200px', margin: '0 auto', p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Connection Manager
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button 
            component={RouterLink} 
            to="/" 
            variant="outlined"
            startIcon={<ArrowBackIcon />}
          >
            Back to Dashboard
          </Button>
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<AddIcon />}
            onClick={handleOpenAddDialog}
          >
            Add Connection
          </Button>
        </Box>
      </Box>
      
      {error && (
        <Typography 
          color="error" 
          sx={{ mb: 2, p: 2, bgcolor: 'error.light', borderRadius: 1, color: 'white' }}
        >
          {error}
        </Typography>
      )}
      
      <TableContainer component={Paper} variant="outlined" sx={{ mb: 4 }}>
        <Table>
          <TableHead>
            <TableRow>
              <StyledTableCell className="header">Name</StyledTableCell>
              <StyledTableCell className="header">Type</StyledTableCell>
              <StyledTableCell className="header">Host</StyledTableCell>
              <StyledTableCell className="header">Port</StyledTableCell>
              <StyledTableCell className="header">Database</StyledTableCell>
              <StyledTableCell className="header">Username</StyledTableCell>
              <StyledTableCell className="header" align="center">Actions</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <StyledTableRow>
                <StyledTableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  <CircularProgress size={40} />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Loading connections...
                  </Typography>
                </StyledTableCell>
              </StyledTableRow>
            ) : connections.length === 0 ? (
              <StyledTableRow>
                <StyledTableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  <Typography variant="body1">
                    No database connections found
                  </Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    Click "Add Connection" to create your first database connection
                  </Typography>
                </StyledTableCell>
              </StyledTableRow>
            ) : (
              connections.map((connection) => (
                <StyledTableRow key={connection.id}>
                  <StyledTableCell>{connection.name}</StyledTableCell>
                  <StyledTableCell>{connection.type}</StyledTableCell>
                  <StyledTableCell>{connection.host}</StyledTableCell>
                  <StyledTableCell>{connection.port}</StyledTableCell>
                  <StyledTableCell>{connection.database}</StyledTableCell>
                  <StyledTableCell>{connection.username}</StyledTableCell>
                  <StyledTableCell align="center">
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                      <Tooltip title="Edit connection">
                        <IconButton 
                          size="small" 
                          color="primary"
                          onClick={() => handleOpenEditDialog(connection)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      
                      <Tooltip title="Delete connection">
                        <IconButton 
                          size="small" 
                          color="error"
                          onClick={() => handleDeleteConnection(connection.id)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </StyledTableCell>
                </StyledTableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <ConnectionDialog 
        open={isAddDialogOpen}
        onClose={handleCloseDialog}
        onConnectionAdded={handleConnectionSaved}
        initialData={editConnection}
        isEditing={!!editConnection}
      />
    </Box>
  );
};

export default ConnectionManager; 