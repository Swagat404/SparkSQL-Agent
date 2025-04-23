import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemText, 
  ListItemIcon,
  Collapse,
  Divider,
  Tabs,
  Tab,
  Avatar,
  IconButton,
  Tooltip,
  Badge,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Button
} from '@mui/material';
import { styled } from '@mui/material/styles';
import HistoryIcon from '@mui/icons-material/History';
import TableChartIcon from '@mui/icons-material/TableChart';
import BarChartIcon from '@mui/icons-material/BarChart';
import StorageIcon from '@mui/icons-material/Storage';
import SchemaIcon from '@mui/icons-material/Schema';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import SearchIcon from '@mui/icons-material/Search';
import DatabaseIcon from '@mui/icons-material/Storage';
import GlassCard from '../ui/GlassCard';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ViewColumnIcon from '@mui/icons-material/ViewColumn';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import EditIcon from '@mui/icons-material/Edit';
import ViewListIcon from '@mui/icons-material/ViewList';
import axios from 'axios';

// Mock data for chat history
const MOCK_CHAT_HISTORY = [
  { id: 1, query: "Show me all orders from the last month", timestamp: "2025-04-20 14:30", resultCount: 145 },
  { id: 2, query: "What were the top selling products?", timestamp: "2025-04-19 11:15", resultCount: 10 },
  { id: 3, query: "Calculate revenue by product category", timestamp: "2025-04-18 09:45", resultCount: 8 },
  { id: 4, query: "Find customers who haven't ordered in 3 months", timestamp: "2025-04-15 16:20", resultCount: 32 }
];

// Mock data for schema
const MOCK_SCHEMA = [
  {
    name: 'customers',
    icon: <StorageIcon fontSize="small" />,
    columns: [
      { name: 'customer_id', type: 'integer', primary: true },
      { name: 'name', type: 'text' },
      { name: 'email', type: 'text' },
      { name: 'country', type: 'text' }
    ]
  },
  {
    name: 'orders',
    icon: <StorageIcon fontSize="small" />,
    columns: [
      { name: 'order_id', type: 'integer', primary: true },
      { name: 'customer_id', type: 'integer', foreign: 'customers.customer_id' },
      { name: 'order_date', type: 'date' },
      { name: 'total_amount', type: 'numeric' }
    ]
  },
  {
    name: 'products',
    icon: <StorageIcon fontSize="small" />,
    columns: [
      { name: 'product_id', type: 'integer', primary: true },
      { name: 'name', type: 'text' },
      { name: 'category', type: 'text' },
      { name: 'price', type: 'numeric' }
    ]
  }
];

// Styled tab for custom appearance
const StyledTab = styled(Tab)(({ theme }) => ({
  minHeight: '48px',
  fontSize: '0.8rem',
  padding: '0 12px',
  '&.Mui-selected': {
    color: theme.palette.primary.main,
  },
}));

// Styled database selector
const DatabaseSelector = styled(Select)(({ theme }) => ({
  '& .MuiSelect-select': {
    padding: '8px 32px 8px 12px',
    fontSize: '0.85rem',
  },
  '& .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: theme.palette.primary.main,
  },
  backgroundColor: 'rgba(30, 34, 48, 0.4)',
}));

// Styled components
const SidebarContainer = styled(Box)(({ theme }) => ({
  height: '100%',
  overflow: 'auto',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: 'rgba(18, 18, 24, 0.6)',
  backdropFilter: 'blur(10px)',
  borderRight: '1px solid rgba(255, 255, 255, 0.05)',
}));

const SidebarHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  display: 'flex',
  alignItems: 'center',
  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
}));

const TabContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
}));

const SidebarTab = styled(Box)(({ theme, active }) => ({
  flex: 1,
  padding: theme.spacing(1.5),
  textAlign: 'center',
  cursor: 'pointer',
  borderBottom: active ? '2px solid #18DCFF' : 'none',
  '&:hover': {
    backgroundColor: active ? 'transparent' : 'rgba(255, 255, 255, 0.03)',
  },
}));

const SearchField = styled(TextField)(({ theme }) => ({
  margin: theme.spacing(2),
  '& .MuiOutlinedInput-root': {
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    borderRadius: theme.shape.borderRadius,
    '& fieldset': {
      borderColor: 'rgba(255, 255, 255, 0.1)',
    },
    '&:hover fieldset': {
      borderColor: 'rgba(255, 255, 255, 0.2)',
    },
    '&.Mui-focused fieldset': {
      borderColor: theme.palette.primary.main,
    },
  },
}));

/**
 * LeftSidebar Component
 * The left sidebar containing database selection, schemas, and query history
 * 
 * @param {Object} props
 * @param {function} props.onHistorySelect - Callback for selecting a history item
 * @param {function} props.onSchemaSelect - Callback for selecting a schema item 
 * @param {Array} props.connections - Available database connections
 * @param {string} props.selectedConnection - ID of the selected connection
 * @param {function} props.onConnectionSelect - Callback for selecting a connection
 * @param {function} props.onAddConnection - Callback for adding a new connection
 * @param {function} props.onEditConnection - Callback for editing a connection
 */
const LeftSidebar = ({ 
  onHistorySelect,
  onSchemaSelect,
  connections = [],
  selectedConnection,
  onConnectionSelect,
  onAddConnection,
  onEditConnection
}) => {
  // State
  const [activeTab, setActiveTab] = useState('schema');
  const [expandedTables, setExpandedTables] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [tables, setTables] = useState([]);
  const [columns, setColumns] = useState({});
  const [loading, setLoading] = useState(false);
  const [historyItems] = useState([
    { query: "Show me all orders", timestamp: "2023-04-10 14:30" },
    { query: "What are the top selling products?", timestamp: "2023-04-10 13:15" },
    { query: "Find customers who haven't ordered in 3 months", timestamp: "2023-04-09 16:45" }
  ]);
  
  // Fetch schema data when selected connection changes
  useEffect(() => {
    if (selectedConnection) {
      fetchSchema(selectedConnection);
    }
  }, [selectedConnection]);
  
  // Fetch schema data from the API
  const fetchSchema = async (connectionId) => {
    if (!connectionId) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`/schema/${connectionId}`);
      
      if (response.data && response.data.tables) {
        setTables(response.data.tables);
        setColumns(response.data.columns || {});
      }
    } catch (error) {
      console.error('Error fetching schema:', error);
      
      // For demo/development - use mock data if API fails
      setTables(['customers', 'orders', 'products', 'order_items']);
      setColumns({
        'customers': ['customer_id', 'name', 'email', 'country'],
        'orders': ['order_id', 'customer_id', 'order_date', 'total_amount', 'status'],
        'products': ['product_id', 'name', 'category', 'price', 'stock'],
        'order_items': ['item_id', 'order_id', 'product_id', 'quantity', 'price_per_unit']
      });
    } finally {
      setLoading(false);
    }
  };
  
  // Toggle table expansion
  const toggleTable = (table) => {
    setExpandedTables(prev => ({
      ...prev,
      [table]: !prev[table]
    }));
  };
  
  // Filter tables and columns based on search query
  const filteredTables = tables.filter(table => 
    table.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  // Get filtered columns for a table
  const getFilteredColumns = (table) => {
    if (!columns[table]) return [];
    
    return columns[table].filter(column =>
      column.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };
  
  // Get active connection name
  const getActiveConnectionName = () => {
    const activeConn = connections.find(conn => conn.id === selectedConnection);
    return activeConn ? `${activeConn.database} (${activeConn.type})` : 'Select Database';
  };

  return (
    <SidebarContainer>
      {/* Database Selection Header */}
      <SidebarHeader>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <ViewListIcon sx={{ mr: 1, color: 'primary.main' }} />
          <FormControl fullWidth size="small">
            <DatabaseSelector
              value={selectedConnection || ''}
              onChange={(e) => onConnectionSelect(e.target.value)}
              displayEmpty
              startAdornment={
                <Box component="span" sx={{ display: 'flex', alignItems: 'center', mr: 1 }}>
                  <StorageIcon fontSize="small" sx={{ color: 'primary.main' }} />
                </Box>
              }
              renderValue={(selected) => {
                if (!selected) {
                  return <Typography variant="body2" color="text.secondary">Select Database</Typography>;
                }
                return getActiveConnectionName();
              }}
            >
              {connections.map((conn) => (
                <MenuItem key={conn.id} value={conn.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                    <Typography variant="body2">{conn.database}</Typography>
                    <Typography variant="caption" color="text.secondary">{conn.type}</Typography>
                  </Box>
                </MenuItem>
              ))}
              
              <Divider sx={{ my: 1 }} />
              
              <MenuItem onClick={onAddConnection}>
                <ListItemIcon>
                  <AddCircleOutlineIcon fontSize="small" />
                </ListItemIcon>
                <Typography variant="body2">Add New Connection</Typography>
              </MenuItem>
              
              {selectedConnection && (
                <MenuItem 
                  onClick={() => {
                    const conn = connections.find(c => c.id === selectedConnection);
                    if (conn) onEditConnection(conn);
                  }}
                >
                  <ListItemIcon>
                    <EditIcon fontSize="small" />
                  </ListItemIcon>
                  <Typography variant="body2">Edit Connection</Typography>
                </MenuItem>
              )}
            </DatabaseSelector>
          </FormControl>
        </Box>
      </SidebarHeader>
      
      {/* Tabs: History, Schema, Visuals */}
      <TabContainer>
        <SidebarTab 
          active={activeTab === 'history'} 
          onClick={() => setActiveTab('history')}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <HistoryIcon fontSize="small" sx={{ mr: 1 }} />
            <Typography variant="body2">History</Typography>
          </Box>
        </SidebarTab>
        
        <SidebarTab 
          active={activeTab === 'schema'} 
          onClick={() => setActiveTab('schema')}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <SchemaIcon fontSize="small" sx={{ mr: 1 }} />
            <Typography variant="body2">Schema</Typography>
          </Box>
        </SidebarTab>
        
        <SidebarTab 
          active={activeTab === 'visuals'} 
          onClick={() => setActiveTab('visuals')}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <BarChartIcon fontSize="small" sx={{ mr: 1 }} />
            <Typography variant="body2">Visuals</Typography>
          </Box>
        </SidebarTab>
      </TabContainer>
      
      {/* Search Field */}
      <SearchField
        size="small"
        placeholder={
          activeTab === 'schema' 
            ? "Search tables and columns" 
            : activeTab === 'history'
              ? "Search query history"
              : "Search visualizations"
        }
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon fontSize="small" sx={{ color: 'text.secondary' }} />
            </InputAdornment>
          ),
        }}
      />
      
      {/* Content based on active tab */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        {/* Schema Tab */}
        {activeTab === 'schema' && (
          <Box>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                <CircularProgress size={30} />
              </Box>
            ) : selectedConnection ? (
              tables.length > 0 ? (
                <List disablePadding>
                  {filteredTables.map((table) => (
                    <React.Fragment key={table}>
                      <ListItem 
                        button 
                        onClick={() => toggleTable(table)}
                        sx={{
                          py: 1,
                          pl: 2,
                          pr: 1,
                          borderLeft: expandedTables[table] ? '3px solid #18DCFF' : '3px solid transparent',
                          bgcolor: expandedTables[table] ? 'rgba(24, 220, 255, 0.05)' : 'transparent',
                        }}
                      >
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <TableChartIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={table} 
                          primaryTypographyProps={{ 
                            variant: 'body2',
                            sx: { fontWeight: expandedTables[table] ? 600 : 400 }
                          }} 
                        />
                        {expandedTables[table] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </ListItem>
                      
                      <Collapse in={expandedTables[table]} timeout="auto" unmountOnExit>
                        <List disablePadding>
                          {getFilteredColumns(table).map((column) => (
                            <ListItem 
                              button
                              key={`${table}.${column}`}
                              sx={{ 
                                py: 0.5, 
                                pl: 6, 
                                '&:hover': {
                                  bgcolor: 'rgba(255, 255, 255, 0.05)',
                                }
                              }}
                              onClick={() => onSchemaSelect && onSchemaSelect(table, column)}
                            >
                              <ListItemIcon sx={{ minWidth: 24 }}>
                                <ViewColumnIcon fontSize="small" />
                              </ListItemIcon>
                              <ListItemText 
                                primary={column} 
                                primaryTypographyProps={{ variant: 'body2' }} 
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Collapse>
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', mt: 4, px: 2 }}>
                  <Typography color="text.secondary" variant="body2">
                    No tables found in this database
                  </Typography>
                </Box>
              )
            ) : (
              <Box sx={{ textAlign: 'center', mt: 4, px: 2 }}>
                <Typography color="text.secondary" variant="body2">
                  Select a database to view schema
                </Typography>
                <Button
                  startIcon={<AddCircleOutlineIcon />}
                  onClick={onAddConnection}
                  sx={{ mt: 2 }}
                  size="small"
                >
                  Add Connection
                </Button>
              </Box>
            )}
          </Box>
        )}
        
        {/* History Tab */}
        {activeTab === 'history' && (
          <List disablePadding>
            {historyItems
              .filter(item => item.query.toLowerCase().includes(searchQuery.toLowerCase()))
              .map((item, index) => (
                <ListItem 
                  button 
                  key={index}
                  onClick={() => onHistorySelect && onHistorySelect(item)}
                  sx={{ 
                    py: 1.5,
                    borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                    '&:hover': {
                      bgcolor: 'rgba(255, 255, 255, 0.05)',
                    }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <HistoryIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.query} 
                    secondary={item.timestamp}
                    primaryTypographyProps={{ variant: 'body2' }}
                    secondaryTypographyProps={{ variant: 'caption' }}
                  />
                </ListItem>
              ))}
          </List>
        )}
        
        {/* Visuals Tab */}
        {activeTab === 'visuals' && (
          <Box sx={{ textAlign: 'center', mt: 4, px: 2 }}>
            <Typography color="text.secondary" variant="body2">
              Run queries to generate visualizations
            </Typography>
            <Box sx={{ mt: 2 }}>
              <BarChartIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
            </Box>
          </Box>
        )}
      </Box>
    </SidebarContainer>
  );
};

export default LeftSidebar; 