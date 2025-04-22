import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Tabs, 
  Tab, 
  IconButton,
  Tooltip,
  Button,
  Menu,
  MenuItem,
  CircularProgress
} from '@mui/material';
import { styled } from '@mui/material/styles';
import TableChartIcon from '@mui/icons-material/TableChart';
import BarChartIcon from '@mui/icons-material/BarChart';
import LineChartIcon from '@mui/icons-material/ShowChart';
import PieChartIcon from '@mui/icons-material/PieChart';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import DataTable from '../ui/DataTable';
import GlassCard from '../ui/GlassCard';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

// Styled tab for custom appearance
const StyledTab = styled(Tab)(({ theme }) => ({
  minHeight: '36px',
  minWidth: '36px',
  padding: '0 10px',
  '&.Mui-selected': {
    color: theme.palette.primary.main,
  },
}));

// Chart colors
const CHART_COLORS = ['#18DCFF', '#9D4EDD', '#3BCBB0', '#FFC857', '#FF5A5A'];

/**
 * RightPanel Component
 * The panel for displaying query results and visualizations
 * 
 * @param {Object} props
 * @param {Array} props.data - Query result data
 * @param {boolean} [props.loading=false] - Whether data is loading
 * @param {number} [props.executionTime=0] - Query execution time in seconds
 * @param {Object} [props.sx] - Additional MUI styling
 */
const RightPanel = ({ 
  data = [],
  loading = false,
  executionTime = 0,
  sx = {} 
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [chartType, setChartType] = useState('bar');
  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  const handleMenuOpen = (event) => {
    setMenuAnchorEl(event.currentTarget);
  };
  
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };
  
  const handleChartTypeChange = (type) => {
    setChartType(type);
    handleMenuClose();
  };
  
  // Prepare data for chart visualization
  const prepareChartData = () => {
    if (!data || data.length === 0) return [];
    
    // Get first two columns for simplicity (x, y) or use a smarter approach
    const columns = Object.keys(data[0]);
    const xKey = columns[0];
    const yKey = columns[1];
    
    // Limit to 10 items for cleaner charts
    return data.slice(0, 10).map(item => ({
      name: String(item[xKey]),
      value: typeof item[yKey] === 'number' ? item[yKey] : 0
    }));
  };
  
  const chartData = prepareChartData();
  
  // Render appropriate chart based on chart type
  const renderChart = () => {
    if (chartData.length === 0) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <Typography color="text.secondary">No data available for visualization</Typography>
        </Box>
      );
    }
    
    switch(chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="name" 
                tick={{ fill: '#E2E8F0', fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fill: '#E2E8F0', fontSize: 12 }} />
              <RechartsTooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(30, 34, 48, 0.9)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  color: '#E2E8F0'
                }} 
              />
              <Bar 
                dataKey="value" 
                fill="url(#barGradient)" 
                radius={[4, 4, 0, 0]}
              />
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#18DCFF" />
                  <stop offset="100%" stopColor="#9D4EDD" />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        );
        
      case 'line':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="name" 
                tick={{ fill: '#E2E8F0', fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fill: '#E2E8F0', fontSize: 12 }} />
              <RechartsTooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(30, 34, 48, 0.9)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  color: '#E2E8F0'
                }} 
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#18DCFF" 
                strokeWidth={2}
                dot={{ 
                  fill: '#18DCFF', 
                  r: 4,
                  strokeWidth: 1,
                  stroke: '#9D4EDD'
                }} 
              />
            </LineChart>
          </ResponsiveContainer>
        );
        
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <RechartsTooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(30, 34, 48, 0.9)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  color: '#E2E8F0'
                }} 
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => <span style={{ color: '#E2E8F0' }}>{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        );
        
      default:
        return (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Typography color="text.secondary">Selected chart type is not available</Typography>
          </Box>
        );
    }
  };
  
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', ...sx }}>
      {/* Header */}
      <Box sx={{ 
        p: 2, 
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Typography variant="h6" fontFamily="'Space Grotesk', sans-serif">
          Results
        </Typography>
        
        {data.length > 0 && !loading && (
          <Typography variant="caption" color="text.secondary">
            {data.length} rows • {executionTime.toFixed(3)}s
          </Typography>
        )}
      </Box>
      
      {/* Tabs */}
      <Box sx={{ 
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        px: 1,
      }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ 
            minHeight: 36,
            '& .MuiTabs-indicator': {
              background: 'linear-gradient(90deg, #18DCFF 0%, #9D4EDD 100%)',
              height: 2,
            }
          }}
        >
          <StyledTab 
            icon={<TableChartIcon fontSize="small" />} 
            aria-label="Table"
            sx={{ minWidth: 56 }}
          />
          <StyledTab 
            icon={
              chartType === 'bar' ? <BarChartIcon fontSize="small" /> :
              chartType === 'line' ? <LineChartIcon fontSize="small" /> :
              <PieChartIcon fontSize="small" />
            } 
            aria-label="Chart"
            sx={{ minWidth: 56 }}
          />
        </Tabs>
        
        {activeTab === 1 && (
          <Box>
            <Tooltip title="Chart options">
              <IconButton size="small" onClick={handleMenuOpen}>
                <MoreVertIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Menu
              anchorEl={menuAnchorEl}
              open={Boolean(menuAnchorEl)}
              onClose={handleMenuClose}
              PaperProps={{
                sx: {
                  backgroundColor: 'background.paper',
                  borderRadius: 1,
                  boxShadow: '0 8px 16px rgba(0, 0, 0, 0.3)',
                }
              }}
            >
              <MenuItem onClick={() => handleChartTypeChange('bar')}>
                <BarChartIcon fontSize="small" sx={{ mr: 1 }} />
                Bar Chart
              </MenuItem>
              <MenuItem onClick={() => handleChartTypeChange('line')}>
                <LineChartIcon fontSize="small" sx={{ mr: 1 }} />
                Line Chart
              </MenuItem>
              <MenuItem onClick={() => handleChartTypeChange('pie')}>
                <PieChartIcon fontSize="small" sx={{ mr: 1 }} />
                Pie Chart
              </MenuItem>
            </Menu>
          </Box>
        )}
      </Box>
      
      {/* Content */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <CircularProgress 
              size={40} 
              sx={{ 
                color: 'primary.main',
                '& .MuiCircularProgress-circle': {
                  strokeLinecap: 'round',
                }
              }} 
            />
          </Box>
        ) : data.length === 0 ? (
          <GlassCard
            intensity="light"
            sx={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}
          >
            <Box sx={{ textAlign: 'center', color: 'text.secondary', p: 3 }}>
              <InfoOutlinedIcon sx={{ fontSize: 48, opacity: 0.5, mb: 2 }} />
              <Typography>
                No results to display yet
              </Typography>
              <Typography variant="body2" sx={{ mt: 1, maxWidth: 300 }}>
                Enter a SQL query or natural language question to get started
              </Typography>
            </Box>
          </GlassCard>
        ) : (
          <>
            {/* Table View */}
            <Box hidden={activeTab !== 0} sx={{ height: '100%' }}>
              <DataTable 
                data={data} 
                allowDownload={true}
              />
            </Box>
            
            {/* Chart View */}
            <Box 
              hidden={activeTab !== 1} 
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              <Box sx={{ flexGrow: 1, minHeight: 300 }}>
                {renderChart()}
              </Box>
              
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<FileDownloadIcon />}
                  sx={{ textTransform: 'none' }}
                >
                  Download Chart
                </Button>
              </Box>
            </Box>
          </>
        )}
      </Box>
    </Box>
  );
};

export default RightPanel; 