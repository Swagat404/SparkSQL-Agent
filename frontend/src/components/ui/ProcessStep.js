import React, { useState } from 'react';
import { Box, Typography, IconButton, Collapse, LinearProgress } from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import PendingIcon from '@mui/icons-material/Pending';
import CodeBlock from './CodeBlock';
import { motion } from 'framer-motion';

/**
 * ProcessStep Component
 * A collapsible step in a multi-step process with animation
 * 
 * @param {Object} props
 * @param {string} props.title - The title of the step
 * @param {string} [props.status='pending'] - Current status ('pending', 'processing', 'completed', 'error')
 * @param {string} [props.explanation] - Text explanation of the step
 * @param {string} [props.code] - Code associated with this step
 * @param {string} [props.language='sql'] - Language of the code
 * @param {boolean} [props.expanded=false] - Whether the step is expanded by default
 * @param {Object} [props.sx] - Additional MUI styling
 */
const ProcessStep = ({
  title,
  status = 'pending',
  explanation,
  code,
  language = 'sql',
  expanded = false,
  sx = {}
}) => {
  const [isExpanded, setIsExpanded] = useState(expanded);

  const getStatusIcon = () => {
    switch(status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'processing':
        return <PendingIcon sx={{ color: '#FFC857' }} />;
      default:
        return <PendingIcon color="disabled" />;
    }
  };
  
  const getStatusColor = () => {
    switch(status) {
      case 'completed': return 'success.main';
      case 'error': return 'error.main';
      case 'processing': return '#FFC857';
      default: return 'text.disabled';
    }
  };

  return (
    <Box 
      sx={{
        border: '1px solid rgba(255, 255, 255, 0.05)',
        borderLeft: `3px solid ${getStatusColor()}`,
        borderRadius: 1,
        mb: 2,
        overflow: 'hidden',
        ...sx
      }}
    >
      <Box 
        component={motion.div}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          cursor: 'pointer',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
          },
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          {getStatusIcon()}
          <Typography variant="subtitle1">
            {title}
          </Typography>
        </Box>
        <IconButton 
          size="small" 
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
        >
          {isExpanded ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
        </IconButton>
      </Box>

      <Collapse in={isExpanded}>
        <Box 
          component={motion.div}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          sx={{ p: 2, pt: 0, borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}
        >
          {status === 'processing' && (
            <LinearProgress 
              sx={{ 
                mb: 2, 
                borderRadius: 1,
                height: 4,
                '& .MuiLinearProgress-bar': {
                  background: 'linear-gradient(90deg, #18DCFF 0%, #9D4EDD 100%)',
                }
              }} 
            />
          )}
          
          {explanation && (
            <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
              {explanation}
            </Typography>
          )}
          
          {code && (
            <CodeBlock 
              code={code} 
              language={language} 
            />
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

export default ProcessStep; 