import React, { useState } from 'react';
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
  InputAdornment
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
import GlassCard from '../ui/GlassCard';

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

/**
 * LeftSidebar Component
 * The sidebar containing chat history, schema explorer, and visual history
 * 
 * @param {Object} props
 * @param {function} [props.onHistorySelect] - Callback when selecting chat history item
 * @param {function} [props.onSchemaSelect] - Callback when selecting schema item
 * @param {Object} [props.sx] - Additional MUI styling
 */
const LeftSidebar = ({ 
  onHistorySelect,
  onSchemaSelect,
  sx = {} 
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [expandedTable, setExpandedTable] = useState(null);
  const [schemaFilter, setSchemaFilter] = useState('');

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const toggleTable = (tableName) => {
    setExpandedTable(expandedTable === tableName ? null : tableName);
  };

  // Filter schema tables and columns based on search term
  const filteredSchema = MOCK_SCHEMA.filter(table => {
    if (!schemaFilter) return true;
    
    const searchTerm = schemaFilter.toLowerCase();
    
    // Check if table name matches
    if (table.name.toLowerCase().includes(searchTerm)) return true;
    
    // Check if any column matches
    return table.columns.some(col => 
      col.name.toLowerCase().includes(searchTerm)
    );
  });

  return (
    <Box 
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        ...sx
      }}
    >
      {/* Header with Logo */}
      <Box 
        sx={{ 
          p: 2, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <Typography 
          variant="h6" 
          component="h1" 
          sx={{ 
            fontWeight: 700, 
            fontFamily: '"Space Grotesk", sans-serif',
            background: 'linear-gradient(90deg, #18DCFF 0%, #9D4EDD 100%)',
            WebkitBackgroundClip: 'text',
            backgroundClip: 'text',
            color: 'transparent'
          }}
        >
          SparkSQL Agent
        </Typography>
      </Box>
      
      {/* Navigation Tabs */}
      <Tabs 
        value={activeTab} 
        onChange={handleTabChange}
        variant="fullWidth" 
        sx={{ 
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          '& .MuiTabs-indicator': {
            background: 'linear-gradient(90deg, #18DCFF 0%, #9D4EDD 100%)',
            height: 3,
          }
        }}
      >
        <StyledTab icon={<HistoryIcon />} label="History" />
        <StyledTab icon={<SchemaIcon />} label="Schema" />
        <StyledTab icon={<BarChartIcon />} label="Visuals" />
      </Tabs>
      
      {/* Tab Content */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {/* Chat History Tab */}
        <Box hidden={activeTab !== 0} sx={{ height: '100%' }}>
          {MOCK_CHAT_HISTORY.length > 0 ? (
            <List sx={{ p: 0 }}>
              {MOCK_CHAT_HISTORY.map((item) => (
                <GlassCard 
                  key={item.id}
                  intensity="light"
                  sx={{ mb: 2, p: 2 }}
                  onClick={() => onHistorySelect && onHistorySelect(item)}
                >
                  <Typography variant="body2" noWrap sx={{ fontWeight: 500 }}>
                    {item.query}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1, alignItems: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      {item.timestamp}
                    </Typography>
                    <Badge 
                      badgeContent={item.resultCount} 
                      color="primary"
                      sx={{ '& .MuiBadge-badge': { fontSize: '0.7rem' } }}
                    >
                      <TableChartIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                    </Badge>
                  </Box>
                </GlassCard>
              ))}
            </List>
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <Typography color="text.secondary">No history yet</Typography>
            </Box>
          )}
        </Box>
        
        {/* Schema Explorer Tab */}
        <Box hidden={activeTab !== 1} sx={{ height: '100%' }}>
          <TextField
            placeholder="Search tables and columns..."
            size="small"
            fullWidth
            value={schemaFilter}
            onChange={(e) => setSchemaFilter(e.target.value)}
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          
          {filteredSchema.length > 0 ? (
            <List 
              sx={{ 
                p: 0,
                '& .MuiListItemButton-root': {
                  borderRadius: 1,
                  mb: 0.5,
                }
              }}
            >
              {filteredSchema.map((table) => (
                <React.Fragment key={table.name}>
                  <ListItemButton
                    onClick={() => toggleTable(table.name)}
                    sx={{
                      backgroundColor: 'rgba(30, 34, 48, 0.4)',
                      '&:hover': {
                        backgroundColor: 'rgba(30, 34, 48, 0.6)',
                      },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {table.icon}
                    </ListItemIcon>
                    <ListItemText 
                      primary={table.name} 
                      primaryTypographyProps={{ 
                        fontWeight: 500,
                        fontFamily: '"JetBrains Mono", monospace',
                        fontSize: '0.875rem'
                      }} 
                    />
                    {expandedTable === table.name ? 
                      <KeyboardArrowUpIcon fontSize="small" /> : 
                      <KeyboardArrowDownIcon fontSize="small" />
                    }
                  </ListItemButton>
                  
                  <Collapse in={expandedTable === table.name} timeout="auto" unmountOnExit>
                    <List component="div" disablePadding dense>
                      {table.columns.map((column) => (
                        <ListItemButton 
                          key={column.name}
                          sx={{ pl: 4 }}
                          onClick={() => onSchemaSelect && onSchemaSelect(table.name, column.name)}
                        >
                          <ListItemText 
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <Typography 
                                  variant="body2" 
                                  fontFamily={'"JetBrains Mono", monospace'}
                                  sx={{ 
                                    color: column.primary ? 'primary.main' : 
                                          column.foreign ? 'secondary.main' : 'text.primary',
                                    fontWeight: column.primary || column.foreign ? 500 : 400,
                                  }}
                                >
                                  {column.name}
                                </Typography>
                                <Typography 
                                  variant="caption" 
                                  fontFamily={'"JetBrains Mono", monospace'}
                                  color="text.secondary"
                                >
                                  {column.type}
                                </Typography>
                              </Box>
                            }
                          />
                        </ListItemButton>
                      ))}
                    </List>
                  </Collapse>
                </React.Fragment>
              ))}
            </List>
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 'calc(100% - 40px)' }}>
              <Typography color="text.secondary">No tables found</Typography>
            </Box>
          )}
        </Box>
        
        {/* Visual History Tab */}
        <Box hidden={activeTab !== 2} sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
          <GlassCard intensity="light" sx={{ p: 0, overflow: 'hidden' }}>
            <Box sx={{ p: 1, borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <Typography variant="caption" color="text.secondary">
                Top Products by Revenue
              </Typography>
            </Box>
            <Box sx={{ p: 0, height: 120, background: 'linear-gradient(180deg, rgba(24, 220, 255, 0.1) 0%, rgba(157, 78, 221, 0.1) 100%)' }}>
              {/* Placeholder for chart thumbnail */}
              <Box sx={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <BarChartIcon sx={{ fontSize: 40, color: 'rgba(255, 255, 255, 0.3)' }} />
              </Box>
            </Box>
          </GlassCard>
          
          <GlassCard intensity="light" sx={{ p: 0, overflow: 'hidden' }}>
            <Box sx={{ p: 1, borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <Typography variant="caption" color="text.secondary">
                Monthly Sales Trend
              </Typography>
            </Box>
            <Box sx={{ p: 0, height: 120, background: 'linear-gradient(180deg, rgba(24, 220, 255, 0.1) 0%, rgba(157, 78, 221, 0.1) 100%)' }}>
              {/* Placeholder for chart thumbnail */}
              <Box sx={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <BarChartIcon sx={{ fontSize: 40, color: 'rgba(255, 255, 255, 0.3)' }} />
              </Box>
            </Box>
          </GlassCard>
        </Box>
      </Box>
      
      {/* User Profile */}
      <Box 
        sx={{ 
          p: 2, 
          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
          display: 'flex',
          alignItems: 'center',
          gap: 1.5
        }}
      >
        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>U</Avatar>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            User
          </Typography>
          <Typography variant="caption" color="text.secondary">
            user@example.com
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default LeftSidebar; 