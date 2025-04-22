import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { Box, Typography, Paper, Divider, CircularProgress, Chip } from '@mui/material';
import { styled } from '@mui/material/styles';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import WarningIcon from '@mui/icons-material/Warning';
import ResultTable from './ResultTable';

const MessageBubble = styled(Paper)(({ theme, sender }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.spacing(1),
  maxWidth: '85%',
  marginBottom: theme.spacing(1),
  backgroundColor: sender === 'user' 
    ? theme.palette.primary.light 
    : (sender === 'system' ? theme.palette.error.light : theme.palette.background.default),
  color: sender === 'user' || sender === 'system' ? theme.palette.common.white : theme.palette.text.primary,
  alignSelf: sender === 'user' ? 'flex-end' : 'flex-start',
  boxShadow: theme.shadows[1],
}));

const ThinkingSection = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.grey[50],
  borderRadius: theme.spacing(1),
  border: `1px solid ${theme.palette.divider}`,
  marginTop: theme.spacing(1),
  fontSize: '0.9rem',
  whiteSpace: 'pre-wrap',
  overflowX: 'auto',
}));

const ChatPanel = ({ 
  messages = [], 
  agentPhases = [], 
  sx = {} 
}) => {
  const messagesEndRef = useRef(null);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return '';
    }
  };

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100%', 
        overflowY: 'auto',
        ...sx
      }}
    >
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          p: 2, 
          flexGrow: 1 
        }}
      >
        {messages.length === 0 ? (
          <Box 
            sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center', 
              height: '100%', 
              opacity: 0.7 
            }}
          >
            <SmartToyIcon sx={{ fontSize: 80, mb: 2, opacity: 0.3 }} />
            <Typography variant="h6" color="textSecondary">
              Start by selecting a database connection
            </Typography>
            <Typography variant="body1" color="textSecondary" sx={{ mt: 1, textAlign: 'center' }}>
              Then ask me anything about your data, like:
              <br />"Show me the top 5 customers by order value"
            </Typography>
          </Box>
        ) : (
          messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: message.sender === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                {message.sender === 'user' ? (
                  <PersonIcon fontSize="small" sx={{ ml: 1, mr: 0.5 }} />
                ) : message.sender === 'system' ? (
                  <WarningIcon fontSize="small" color="error" sx={{ mr: 0.5 }} />
                ) : (
                  <SmartToyIcon fontSize="small" color="primary" sx={{ mr: 0.5 }} />
                )}
                <Typography variant="caption" color="textSecondary">
                  {message.sender === 'user' 
                    ? 'You' 
                    : (message.sender === 'system' ? 'System' : 'SQL Agent')}
                </Typography>
                <Typography variant="caption" color="textSecondary" sx={{ ml: 1 }}>
                  {formatTimestamp(message.timestamp)}
                </Typography>
              </Box>

              <MessageBubble sender={message.sender} elevation={1}>
                <Typography variant="body1" component="div">
                  {message.text}
                </Typography>
                
                {/* Show result table if results exist */}
                {message.sender === 'ai' && message.result && message.result.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <ResultTable data={message.result} />
                  </Box>
                )}
                
                {/* Show execution info if available */}
                {message.sender === 'ai' && message.executionTime && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                    <Chip 
                      size="small" 
                      label={`Execution time: ${message.executionTime.toFixed(2)}s`} 
                      variant="outlined"
                    />
                    <Chip 
                      size="small" 
                      label={`${message.result ? message.result.length : 0} results`} 
                      variant="outlined"
                    />
                  </Box>
                )}
              </MessageBubble>
              
              {/* Show thinking process for AI messages */}
              {message.sender === 'ai' && message.thinking && (
                <Box sx={{ alignSelf: 'stretch', mt: 1, px: 2 }}>
                  <details>
                    <summary>
                      <Typography 
                        variant="caption" 
                        component="span" 
                        sx={{ 
                          cursor: 'pointer', 
                          color: 'text.secondary',
                          '&:hover': { textDecoration: 'underline' }
                        }}
                      >
                        Show AI thinking process
                      </Typography>
                    </summary>
                    <ThinkingSection>
                      {message.thinking}
                    </ThinkingSection>
                  </details>
                </Box>
              )}
            </Box>
          ))
        )}
        
        {/* Show agent phases when loading */}
        {agentPhases.length > 0 && (
          <Box sx={{ mt: 2, alignSelf: 'flex-start', maxWidth: '85%' }}>
            <Paper 
              sx={{ 
                p: 2, 
                bgcolor: 'background.default', 
                borderRadius: 2,
                border: '1px solid',
                borderColor: 'divider' 
              }}
            >
              <Typography variant="subtitle2" gutterBottom>
                Processing your request...
              </Typography>
              
              {agentPhases.map((phase, index) => (
                <Box key={index} sx={{ mb: 1 }}>
                  <Typography 
                    variant="caption" 
                    component="div" 
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      color: 'text.secondary' 
                    }}
                  >
                    <CircularProgress size={12} thickness={6} sx={{ mr: 1 }} />
                    {phase.phase.replace(/_/g, ' ')}
                  </Typography>
                </Box>
              ))}
            </Paper>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>
    </Box>
  );
};

ChatPanel.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      text: PropTypes.string.isRequired,
      sender: PropTypes.oneOf(['user', 'ai', 'system']).isRequired,
      timestamp: PropTypes.string,
      result: PropTypes.array,
      executionTime: PropTypes.number,
      thinking: PropTypes.string
    })
  ),
  agentPhases: PropTypes.arrayOf(
    PropTypes.shape({
      phase: PropTypes.string.isRequired,
      content: PropTypes.string,
      status: PropTypes.string
    })
  ),
  sx: PropTypes.object
};

export default ChatPanel; 