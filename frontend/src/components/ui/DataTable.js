import React, { useState } from 'react';
import { 
  Box, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  TablePagination,
  TableSortLabel,
  Paper,
  Typography,
  IconButton,
  Tooltip
} from '@mui/material';
import { styled } from '@mui/material/styles';
import FileDownloadIcon from '@mui/icons-material/FileDownload';

// Styled components
const StyledTableCell = styled(TableCell)(({ theme }) => ({
  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
  padding: '12px 16px',
}));

const StyledTableHeadCell = styled(StyledTableCell)(({ theme }) => ({
  backgroundColor: 'rgba(13, 15, 24, 0.6)',
  fontWeight: 600,
  color: theme.palette.primary.main,
  whiteSpace: 'nowrap',
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  '&:nth-of-type(odd)': {
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
  },
  '&:hover': {
    backgroundColor: 'rgba(24, 220, 255, 0.05)',
  },
  transition: 'background-color 0.2s',
}));

/**
 * DataTable Component
 * A modern data table for displaying query results with sorting and pagination
 * 
 * @param {Object} props
 * @param {Array} props.data - Array of data objects
 * @param {number} [props.rowsPerPageOptions=[10, 25, 50, 100]] - Options for rows per page
 * @param {number} [props.defaultRowsPerPage=10] - Default rows per page
 * @param {Object} [props.sx] - Additional MUI styling
 * @param {boolean} [props.allowDownload=true] - Whether to allow downloading data as CSV
 */
const DataTable = ({
  data = [],
  rowsPerPageOptions = [10, 25, 50, 100],
  defaultRowsPerPage = 10,
  sx = {},
  allowDownload = true,
}) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(defaultRowsPerPage);
  const [orderBy, setOrderBy] = useState(null);
  const [order, setOrder] = useState('asc');
  
  // Handle empty data
  if (!data || data.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center', ...sx }}>
        <Typography color="text.secondary">No data to display</Typography>
      </Box>
    );
  }
  
  // Extract column headers from first data item
  const columns = Object.keys(data[0]);
  
  // Handle sorting
  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };
  
  // Sort the data based on orderBy and order
  const sortedData = React.useMemo(() => {
    if (!orderBy) return data;
    
    return [...data].sort((a, b) => {
      const aValue = a[orderBy];
      const bValue = b[orderBy];
      
      // Handle null and undefined values
      if (aValue == null) return order === 'asc' ? -1 : 1;
      if (bValue == null) return order === 'asc' ? 1 : -1;
      
      // Handle numeric values
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return order === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      // Handle date values
      if (aValue instanceof Date && bValue instanceof Date) {
        return order === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      // Handle string values
      return order === 'asc'
        ? String(aValue).localeCompare(String(bValue))
        : String(bValue).localeCompare(String(aValue));
    });
  }, [data, orderBy, order]);
  
  // Pagination
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Download as CSV
  const downloadCSV = () => {
    if (!data || data.length === 0) return;
    
    // Create CSV content
    const headers = columns.join(',');
    const rows = data.map(row => 
      columns.map(column => {
        const value = row[column];
        // Handle strings with commas by wrapping in quotes
        if (typeof value === 'string' && value.includes(',')) {
          return `"${value}"`;
        }
        return value;
      }).join(',')
    ).join('\n');
    
    const csvContent = `${headers}\n${rows}`;
    
    // Create and download the file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `data-export-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  return (
    <Box sx={{ width: '100%', ...sx }}>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
        {allowDownload && (
          <Tooltip title="Download as CSV">
            <IconButton onClick={downloadCSV} size="small" color="primary">
              <FileDownloadIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>
      
      <Paper sx={{ width: '100%', overflow: 'hidden', backgroundColor: 'rgba(30, 34, 48, 0.3)' }}>
        <TableContainer sx={{ maxHeight: 500 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <StyledTableHeadCell key={column}>
                    <TableSortLabel
                      active={orderBy === column}
                      direction={orderBy === column ? order : 'asc'}
                      onClick={() => handleRequestSort(column)}
                      sx={{
                        '& .MuiTableSortLabel-icon': {
                          color: 'primary.main !important',
                        },
                      }}
                    >
                      {column}
                    </TableSortLabel>
                  </StyledTableHeadCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedData
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((row, rowIndex) => (
                  <StyledTableRow key={rowIndex}>
                    {columns.map((column) => (
                      <StyledTableCell key={`${rowIndex}-${column}`}>
                        {row[column] !== null && row[column] !== undefined
                          ? String(row[column])
                          : ''}
                      </StyledTableCell>
                    ))}
                  </StyledTableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={rowsPerPageOptions}
          component="div"
          count={data.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          sx={{ 
            borderTop: '1px solid rgba(255, 255, 255, 0.05)',
            '& .MuiTablePagination-select': {
              paddingLeft: 1,
              paddingRight: 1,
            },
          }}
        />
      </Paper>
    </Box>
  );
};

export default DataTable; 