import React from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Paper,
  Typography,
  IconButton,
  Tooltip
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import FileDownloadIcon from '@mui/icons-material/FileDownload';

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  borderBottom: `1px solid ${theme.palette.divider}`,
  padding: theme.spacing(1),
  '&.header': {
    backgroundColor: theme.palette.grey[100],
    fontWeight: 600,
    color: theme.palette.text.primary,
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

const ResultTable = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', p: 2, color: 'text.secondary' }}>
        <Typography variant="body2">No data available</Typography>
      </Box>
    );
  }

  // Extract column headers from first row
  const columns = Object.keys(data[0]);

  // Format cell value for display
  const formatCellValue = (value) => {
    if (value === null || value === undefined) {
      return <Typography variant="body2" color="text.disabled">NULL</Typography>;
    }
    
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    
    return value.toString();
  };

  // Copy all data as CSV
  const copyAsCSV = () => {
    // Header row
    const headerRow = columns.join(',');
    
    // Data rows
    const dataRows = data.map(row => 
      columns.map(col => {
        const value = row[col];
        // Handle null values and quote strings containing commas
        if (value === null || value === undefined) return '';
        const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
        return stringValue.includes(',') ? `"${stringValue}"` : stringValue;
      }).join(',')
    );
    
    // Combine header and data
    const csv = [headerRow, ...dataRows].join('\n');
    
    // Copy to clipboard
    navigator.clipboard.writeText(csv)
      .then(() => {
        console.log('Data copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy data', err);
      });
  };

  // Download data as CSV
  const downloadCSV = () => {
    // Header row
    const headerRow = columns.join(',');
    
    // Data rows
    const dataRows = data.map(row => 
      columns.map(col => {
        const value = row[col];
        // Handle null values and quote strings containing commas
        if (value === null || value === undefined) return '';
        const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
        return stringValue.includes(',') ? `"${stringValue}"` : stringValue;
      }).join(',')
    );
    
    // Combine header and data
    const csv = [headerRow, ...dataRows].join('\n');
    
    // Create and download file
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `query-results-${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle2">
          Query Results ({data.length} {data.length === 1 ? 'row' : 'rows'})
        </Typography>
        <Box>
          <Tooltip title="Copy as CSV">
            <IconButton size="small" onClick={copyAsCSV}>
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Download CSV">
            <IconButton size="small" onClick={downloadCSV}>
              <FileDownloadIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      <TableContainer 
        component={Paper} 
        variant="outlined"
        sx={{ 
          maxHeight: 300,
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0,0,0,0.2)',
            borderRadius: '4px',
          },
        }}
      >
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <StyledTableCell key={column} className="header">
                  {column}
                </StyledTableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, rowIndex) => (
              <StyledTableRow key={rowIndex}>
                {columns.map((column) => (
                  <StyledTableCell key={`${rowIndex}-${column}`}>
                    {formatCellValue(row[column])}
                  </StyledTableCell>
                ))}
              </StyledTableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

ResultTable.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired
};

export default ResultTable; 