import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';
import { Link } from 'react-router-dom';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import HomeOutlinedIcon from '@mui/icons-material/HomeOutlined';

const NotFound = () => {
  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          textAlign: 'center',
          py: 8,
        }}
      >
        <ErrorOutlineIcon 
          sx={{ 
            fontSize: 120, 
            color: 'primary.main',
            mb: 3,
          }} 
        />
        
        <Typography
          variant="h1"
          sx={{
            fontSize: { xs: '6rem', md: '10rem' },
            fontWeight: 700,
            background: 'linear-gradient(90deg, #18DCFF, #9D4EDD)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 2,
          }}
        >
          404
        </Typography>
        
        <Typography
          variant="h4"
          color="textPrimary"
          sx={{
            fontWeight: 600,
            mb: 3,
          }}
        >
          Page Not Found
        </Typography>
        
        <Typography
          variant="body1"
          color="textSecondary"
          sx={{
            maxWidth: 480,
            mb: 6,
          }}
        >
          The page you're looking for doesn't exist or has been moved.
          Please check the URL or navigate back to the dashboard.
        </Typography>
        
        <Button
          component={Link}
          to="/"
          variant="contained"
          size="large"
          startIcon={<HomeOutlinedIcon />}
          sx={{
            px: 4,
            py: 1.5,
          }}
        >
          Back to Home
        </Button>
      </Box>
    </Container>
  );
};

export default NotFound; 