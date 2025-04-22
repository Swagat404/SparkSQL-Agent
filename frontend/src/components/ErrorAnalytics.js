import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton
} from '@mui/material';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Link } from 'react-router-dom';
import { Info as InfoIcon } from '@mui/icons-material';

// Mock data for demo
const mockErrorData = [
  { id: 1, type: 'Syntax Error', message: 'Unexpected token near SELECT', query: 'SELCT * FROM users', timestamp: '2025-04-21T14:30:00' },
  { id: 2, type: 'Table Not Found', message: 'Table "customer" does not exist', query: 'SELECT * FROM customer', timestamp: '2025-04-21T15:45:00' },
  { id: 3, type: 'Column Not Found', message: 'Column "emails" does not exist', query: 'SELECT emails FROM users', timestamp: '2025-04-22T09:15:00' },
  { id: 4, type: 'Syntax Error', message: 'Missing parenthesis', query: 'SELECT * FROM orders WHERE id = 1 AND status = "completed"', timestamp: '2025-04-22T10:20:00' },
  { id: 5, type: 'Connection Error', message: 'Failed to connect to database', query: 'SELECT * FROM products', timestamp: '2025-04-22T11:30:00' },
];

const errorTypeData = [
  { name: 'Syntax Error', value: 2 },
  { name: 'Table Not Found', value: 1 },
  { name: 'Column Not Found', value: 1 },
  { name: 'Connection Error', value: 1 },
];

const errorByDayData = [
  { day: 'Apr 21', count: 2 },
  { day: 'Apr 22', count: 3 },
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const ErrorAnalytics = () => {
  const [errorLogs, setErrorLogs] = useState([]);
  const [selectedError, setSelectedError] = useState(null);

  useEffect(() => {
    // In a real app, fetch error logs from API
    setErrorLogs(mockErrorData);
  }, []);

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          SQL Error Analytics
        </Typography>
        <Button 
          variant="outlined" 
          component={Link}
          to="/"
        >
          Back to Dashboard
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Error Charts */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Errors by Type
            </Typography>
            <PieChart width={400} height={300}>
              <Pie
                data={errorTypeData}
                cx={200}
                cy={150}
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {errorTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </Paper>
        </Grid>

        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Errors by Day
            </Typography>
            <BarChart
              width={400}
              height={300}
              data={errorByDayData}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#8884d8" name="Error Count" />
            </BarChart>
          </Paper>
        </Grid>

        {/* Error Log Table */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, width: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Error Log
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Error Type</TableCell>
                    <TableCell>Message</TableCell>
                    <TableCell>SQL Query</TableCell>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {errorLogs.map((error) => (
                    <TableRow key={error.id}>
                      <TableCell>
                        <Chip 
                          label={error.type} 
                          color={
                            error.type === 'Syntax Error' ? 'error' :
                            error.type === 'Connection Error' ? 'warning' :
                            'primary'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{error.message}</TableCell>
                      <TableCell>
                        <Box sx={{ maxWidth: 200, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {error.query}
                        </Box>
                      </TableCell>
                      <TableCell>{formatTimestamp(error.timestamp)}</TableCell>
                      <TableCell>
                        <IconButton 
                          size="small"
                          onClick={() => setSelectedError(error)}
                        >
                          <InfoIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Selected Error Details */}
        {selectedError && (
          <Grid item xs={12}>
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Error Details
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  Type: {selectedError.type}
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  Message: {selectedError.message}
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  Time: {formatTimestamp(selectedError.timestamp)}
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  SQL Query:
                </Typography>
                <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                    {selectedError.query}
                  </pre>
                </Paper>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Suggested Fix:
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: '#e3f2fd' }}>
                    {selectedError.type === 'Syntax Error' && selectedError.query.includes('SELCT') && (
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        Use "SELECT" instead of "SELCT":
                        {"\n"}
                        SELECT * FROM users
                      </pre>
                    )}
                    {selectedError.type === 'Table Not Found' && (
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        Make sure table exists or try using "customers" instead of "customer":
                        {"\n"}
                        SELECT * FROM customers
                      </pre>
                    )}
                    {selectedError.type === 'Column Not Found' && (
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        Use "email" instead of "emails":
                        {"\n"}
                        SELECT email FROM users
                      </pre>
                    )}
                    {selectedError.type === 'Connection Error' && (
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        Check database connection settings and make sure the database server is running.
                      </pre>
                    )}
                  </Paper>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default ErrorAnalytics; 