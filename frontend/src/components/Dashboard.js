import React from 'react';
import { Box, Typography, Grid, Paper, Button, Card, CardContent, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import StorageIcon from '@mui/icons-material/Storage';
import CodeIcon from '@mui/icons-material/Code';
import TimelineIcon from '@mui/icons-material/Timeline';
import SettingsIcon from '@mui/icons-material/Settings';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed', error);
    }
  };

  const features = [
    {
      title: 'Connection Management',
      description: 'Connect to your Spark SQL databases and manage your connections.',
      icon: <StorageIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      action: () => navigate('/connections'),
    },
    {
      title: 'Query Interface',
      description: 'Write, optimize, and execute your Spark SQL queries with AI assistance.',
      icon: <CodeIcon sx={{ fontSize: 40, color: 'secondary.main' }} />,
      action: () => navigate('/query'),
    },
    {
      title: 'Error Analytics',
      description: 'Analyze and troubleshoot query errors with intelligent diagnostics.',
      icon: <TimelineIcon sx={{ fontSize: 40, color: 'success.main' }} />,
      action: () => navigate('/analytics'),
    },
    {
      title: 'Settings',
      description: 'Configure your workspace preferences and API connections.',
      icon: <SettingsIcon sx={{ fontSize: 40, color: 'warning.main' }} />,
      action: () => navigate('/settings'),
    },
  ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            mb: 5,
          }}
        >
          <Box>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                mb: 1,
              }}
            >
              Welcome, <span className="gradient-text">{user?.username || 'User'}</span>
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage your SparkSQL queries and connections from this dashboard.
            </Typography>
          </Box>
          <Button
            variant="outlined"
            color="primary"
            onClick={handleLogout}
          >
            Sign Out
          </Button>
        </Box>

        <Grid container spacing={3}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card 
                sx={{ 
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.3s',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 8,
                  },
                  borderRadius: 2,
                  overflow: 'hidden',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                }}
              >
                <Box
                  sx={{
                    p: 3,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'rgba(0, 0, 0, 0.2)',
                  }}
                >
                  {feature.icon}
                </Box>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" component="h2" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {feature.description}
                  </Typography>
                  <Button 
                    variant="contained" 
                    size="small"
                    onClick={feature.action}
                    sx={{ mt: 'auto' }}
                  >
                    Open
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Paper
          sx={{ 
            p: 3,
            mt: 4,
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(90deg, rgba(24, 220, 255, 0.1) 0%, rgba(157, 78, 221, 0.1) 100%)',
            border: '1px solid rgba(24, 220, 255, 0.2)',
            borderRadius: 2,
          }}
        >
          <Box sx={{ mb: { xs: 2, sm: 0 } }}>
            <Typography variant="h6" gutterBottom>
              Ready to start a new query?
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Use our AI-powered query interface to write and optimize your Spark SQL queries.
            </Typography>
          </Box>
          <Button 
            variant="contained"
            size="large"
            onClick={() => navigate('/query')}
          >
            Start Query
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default Dashboard; 