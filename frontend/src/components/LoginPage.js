import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Container,
  Link as MuiLink,
  InputAdornment,
  IconButton,
  Divider
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import GlassCard from './ui/GlassCard';

// Styled components
const StyledTextField = styled(TextField)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  '& .MuiOutlinedInput-root': {
    borderRadius: 12,
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(10px)',
    '& fieldset': {
      borderColor: 'rgba(255, 255, 255, 0.1)',
    },
    '&:hover fieldset': {
      borderColor: theme.palette.primary.main,
    },
    '&.Mui-focused fieldset': {
      borderColor: theme.palette.primary.main,
    },
  },
}));

const GradientBackgroundBlob = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: '20%',
  left: '50%',
  transform: 'translateX(-50%)',
  width: '80%',
  height: '60%',
  background: 'radial-gradient(circle, rgba(24, 220, 255, 0.15) 0%, rgba(157, 78, 221, 0.15) 100%)',
  borderRadius: '100%',
  filter: 'blur(100px)',
  zIndex: -1,
}));

const LoginPage = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    setError('');
  };

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // In a real application, you would call your authentication API here
      // This is just a simulation for the purposes of this demo
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      // Temporarily simulate login success and store some user info
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('user', JSON.stringify({
        name: 'Demo User',
        email: formData.email
      }));
      
      // Navigate to the main application page
      navigate('/app');
    } catch (err) {
      setError('Invalid credentials. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      bgcolor: 'background.default',
      px: 2
    }}>
      <GradientBackgroundBlob />
      
      {/* Back to home link */}
      <Box
        sx={{
          position: 'absolute',
          top: 24,
          left: 24,
        }}
      >
        <Button
          component={Link}
          to="/"
          startIcon={<ArrowBackIcon />}
          color="inherit"
          sx={{ textTransform: 'none' }}
        >
          Back to Home
        </Button>
      </Box>
      
      <Container maxWidth="xs">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <GlassCard intensity={0.2} glow>
            <Box
              component="form"
              onSubmit={handleSubmit}
              sx={{
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <Box sx={{ textAlign: 'center', mb: 4 }}>
                <Typography 
                  variant="h4" 
                  component="h1" 
                  gutterBottom
                  fontWeight={700}
                  fontFamily='"Space Grotesk", sans-serif'
                >
                  Welcome Back
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Enter your credentials to access your account
                </Typography>
              </Box>
              
              {error && (
                <Typography 
                  color="error" 
                  variant="body2" 
                  sx={{ 
                    mb: 2, 
                    textAlign: 'center',
                    p: 1,
                    borderRadius: 1,
                    bgcolor: 'rgba(244, 67, 54, 0.1)'
                  }}
                >
                  {error}
                </Typography>
              )}
              
              <StyledTextField
                fullWidth
                label="Email Address"
                name="email"
                value={formData.email}
                onChange={handleChange}
                autoComplete="email"
                required
                autoFocus
              />
              
              <StyledTextField
                fullWidth
                label="Password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleChange}
                autoComplete="current-password"
                required
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={handleClickShowPassword}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
              
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                <MuiLink
                  component={Link}
                  to="/forgot-password"
                  variant="body2"
                  underline="hover"
                  sx={{ color: 'primary.main' }}
                >
                  Forgot password?
                </MuiLink>
              </Box>
              
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={isLoading}
                sx={{
                  borderRadius: 28,
                  py: 1.5,
                  mb: 3,
                  position: 'relative',
                  overflow: 'hidden',
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: '-100%',
                    width: '200%',
                    height: '100%',
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                    animation: isLoading ? 'ripple 1.5s infinite' : 'none',
                  },
                  '@keyframes ripple': {
                    '0%': {
                      left: '-100%',
                    },
                    '100%': {
                      left: '100%',
                    },
                  },
                }}
              >
                {isLoading ? 'Signing In...' : 'Sign In'}
              </Button>
              
              <Divider sx={{ my: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  OR
                </Typography>
              </Divider>
              
              <Button
                fullWidth
                variant="outlined"
                component={Link}
                to="/signup"
                sx={{
                  borderRadius: 28,
                  py: 1.5,
                  textTransform: 'none',
                }}
              >
                Create a New Account
              </Button>
              
              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  By signing in, you agree to our {' '}
                  <MuiLink component={Link} to="/terms" underline="hover" sx={{ color: 'primary.main' }}>
                    Terms of Service
                  </MuiLink>
                  {' '} and {' '}
                  <MuiLink component={Link} to="/privacy" underline="hover" sx={{ color: 'primary.main' }}>
                    Privacy Policy
                  </MuiLink>
                </Typography>
              </Box>
            </Box>
          </GlassCard>
        </motion.div>
      </Container>
    </Box>
  );
};

export default LoginPage; 