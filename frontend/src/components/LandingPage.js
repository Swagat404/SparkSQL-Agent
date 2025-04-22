import React from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Container, 
  Grid, 
  Card, 
  CardContent,
  Divider
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import StorageIcon from '@mui/icons-material/Storage';
import CodeIcon from '@mui/icons-material/Code';
import VisibilityIcon from '@mui/icons-material/Visibility';
import TerminalIcon from '@mui/icons-material/Terminal';
import GlassCard from './ui/GlassCard';

// Styled components
const HeroSection = styled(Box)(({ theme }) => ({
  minHeight: '85vh',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  position: 'relative',
  overflow: 'hidden',
}));

const GradientBackgroundTop = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: -300,
  left: '50%',
  transform: 'translateX(-50%)',
  width: '140%',
  height: '600px',
  background: 'radial-gradient(circle, rgba(24, 220, 255, 0.15) 0%, rgba(157, 78, 221, 0.15) 100%)',
  borderRadius: '100%',
  filter: 'blur(100px)',
  zIndex: -1,
}));

const FeatureCard = styled(GlassCard)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'flex-start',
  alignItems: 'flex-start',
  transition: 'transform 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-5px)',
  },
}));

// Animation variants
const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { 
      duration: 0.6,
    } 
  }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2
    }
  }
};

const LandingPage = () => {
  return (
    <Box sx={{ 
      minHeight: '100vh', 
      bgcolor: 'background.default',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <GradientBackgroundTop />
      
      {/* Particles background effect */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: -1,
          opacity: 0.6,
          background: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 400 400\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'0.05\'%3E%3Ccircle cx=\'20\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'20\' r=\'1\'/%3E%3Ccircle cx=\'20\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'60\' r=\'1\'/%3E%3Ccircle cx=\'20\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'100\' r=\'1\'/%3E%3Ccircle cx=\'20\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'140\' r=\'1\'/%3E%3Ccircle cx=\'20\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'180\' r=\'1\'/%3E%3Ccircle cx=\'20\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'220\' r=\'1\'/%3E%3Ccircle cx=\'20\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'260\' r=\'1\'/%3E%3Ccircle cx=\'20\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'300\' r=\'1\'/%3E%3Ccircle cx=\'20\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'340\' r=\'1\'/%3E%3Ccircle cx=\'20\' cy=\'380\' r=\'1\'/%3E%3Ccircle cx=\'60\' cy=\'380\' r=\'1\'/%3E%3Ccircle cx=\'100\' cy=\'380\' r=\'1\'/%3E%3Ccircle cx=\'140\' cy=\'380\' r=\'1\'/%3E%3Ccircle cx=\'180\' cy=\'380\' r=\'1\'/%3E%3Ccircle cx=\'220\' cy=\'380\' r=\'1\'/%3E%3Ccircle cx=\'260\' cy=\'380\' r=\'1\'/%3E%3Ccircle cx=\'300\' cy=\'380\' r=\'1\'/%3E%3Ccircle cx=\'340\' cy=\'380\' r=\'1\'/%3E%3Ccircle cx=\'380\' cy=\'380\' r=\'1\'/%3E%3C/g%3E%3C/svg%3E")',
        }}
      />

      {/* Header */}
      <Box
        component={motion.div}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        sx={{
          p: 3,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography 
          variant="h5" 
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
        
        <Button 
          component={Link} 
          to="/login" 
          variant="outlined"
          sx={{ 
            borderRadius: 28, 
            px: 3,
            '&:hover': {
              boxShadow: '0 0 10px rgba(24, 220, 255, 0.5)',
            }
          }}
        >
          Login
        </Button>
      </Box>
      
      {/* Hero Section */}
      <HeroSection>
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Box
                component={motion.div}
                initial="hidden"
                animate="visible"
                variants={staggerContainer}
              >
                <motion.div variants={fadeIn}>
                  <Typography
                    variant="h2"
                    component="h2"
                    sx={{
                      fontWeight: 700,
                      mb: 2,
                      fontFamily: '"Space Grotesk", sans-serif',
                      fontSize: { xs: '2.5rem', md: '3.5rem' },
                    }}
                  >
                    <span className="gradient-text">Chat with your data</span> using natural language
                  </Typography>
                </motion.div>
                
                <motion.div variants={fadeIn}>
                  <Typography
                    variant="h6"
                    color="text.secondary"
                    sx={{ mb: 4, fontWeight: 400, maxWidth: 550 }}
                  >
                    SparkSQL Agent translates natural language into powerful SQL queries and PySpark transformations.
                    Connect, query, and visualize your data effortlessly.
                  </Typography>
                </motion.div>
                
                <motion.div variants={fadeIn}>
                  <Button
                    component={Link}
                    to="/login"
                    variant="contained"
                    size="large"
                    sx={{
                      borderRadius: 28,
                      px: 4,
                      py: 1.5,
                      fontSize: '1rem',
                      fontWeight: 500,
                      mb: 3,
                    }}
                  >
                    Try It Now
                  </Button>
                </motion.div>
                
                <motion.div variants={fadeIn}>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Supports MySQL and PostgreSQL databases, with more coming soon.
                  </Typography>
                </motion.div>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box
                component={motion.div}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.7, delay: 0.2 }}
                sx={{
                  position: 'relative',
                  width: '100%',
                }}
              >
                <GlassCard
                  glow
                  sx={{
                    p: 0,
                    overflow: 'hidden',
                    height: { xs: 300, md: 400 }
                  }}
                >
                  <Box sx={{ 
                    p: 0, 
                    height: '100%', 
                    background: 'linear-gradient(135deg, rgba(24, 220, 255, 0.1) 0%, rgba(157, 78, 221, 0.1) 100%)',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center'
                  }}>
                    <Typography color="text.secondary" variant="body2">
                      Interactive demo preview
                    </Typography>
                  </Box>
                </GlassCard>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </HeroSection>
      
      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
        >
          <Typography
            variant="h3"
            component="h3"
            align="center"
            sx={{
              fontWeight: 700,
              mb: 6,
              fontFamily: '"Space Grotesk", sans-serif',
            }}
          >
            <span className="gradient-text">Features</span>
          </Typography>
        </motion.div>
        
        <Grid container spacing={4}>
          {[
            {
              icon: <StorageIcon fontSize="large" sx={{ color: '#18DCFF' }} />,
              title: 'Multiple Database Support',
              description: 'Connect to MySQL, PostgreSQL, and other databases with a simple configuration.'
            },
            {
              icon: <TerminalIcon fontSize="large" sx={{ color: '#9D4EDD' }} />,
              title: 'Natural Language to SQL',
              description: 'Ask questions in plain English and get SQL queries that answer your data questions.'
            },
            {
              icon: <CodeIcon fontSize="large" sx={{ color: '#3BCBB0' }} />,
              title: 'PySpark Transformations',
              description: 'Automatically generate optimized PySpark code for complex data transformations.'
            },
            {
              icon: <VisibilityIcon fontSize="large" sx={{ color: '#FFC857' }} />,
              title: 'Interactive Visualizations',
              description: 'Automatically visualize your query results with customizable charts and graphs.'
            }
          ].map((feature, index) => (
            <Grid key={index} item xs={12} sm={6} md={3}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <FeatureCard>
                  <Box sx={{ mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom fontFamily="'Space Grotesk', sans-serif">
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </FeatureCard>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>
      
      {/* Footer */}
      <Box 
        component="footer" 
        sx={{ 
          py: 4, 
          textAlign: 'center',
          borderTop: '1px solid rgba(255, 255, 255, 0.05)'
        }}
      >
        <Container>
          <Typography variant="body2" color="text.secondary">
            © {new Date().getFullYear()} SparkSQL Agent. All rights reserved.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage; 