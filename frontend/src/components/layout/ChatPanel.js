import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  IconButton, 
  CircularProgress,
  Tooltip,
  Divider,
  Chip,
  Menu,
  MenuItem,
  Select,
  FormControl
} from '@mui/material';
import { styled } from '@mui/material/styles';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import SettingsIcon from '@mui/icons-material/Settings';
import DatabaseIcon from '@mui/icons-material/Storage';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import { motion } from 'framer-motion';
import GlassCard from '../ui/GlassCard';
import ProcessStep from '../ui/ProcessStep';
import CodeBlock from '../ui/CodeBlock';
import AgentPhasesDisplay from '../ui/AgentPhaseDisplay';

// Styled components
const ChatContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  maxWidth: '900px',
  margin: '0 auto',
}));

const MessageContainer = styled(Box)(({ theme, sender }) => ({
  display: 'flex',
  flexDirection: sender === 'user' ? 'row-reverse' : 'row',
  marginBottom: theme.spacing(2),
}));

const MessageContent = styled(Box)(({ theme, sender }) => ({
  maxWidth: '70%',
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: sender === 'user' 
    ? 'rgba(24, 220, 255, 0.15)'
    : 'rgba(30, 34, 48, 0.5)',
  backdropFilter: 'blur(8px)',
  border: '1px solid',
  borderColor: sender === 'user' 
    ? 'rgba(24, 220, 255, 0.2)'
    : 'rgba(255, 255, 255, 0.05)',
}));

const InputContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  marginTop: 'auto',
  padding: theme.spacing(2),
}));

// Database context chip styling
const DatabaseChip = styled(Chip)(({ theme }) => ({
  height: 24,
  fontSize: '0.75rem',
  backgroundColor: 'rgba(24, 220, 255, 0.1)',
  borderColor: 'rgba(24, 220, 255, 0.3)',
  '& .MuiChip-label': { 
    padding: '0 8px',
    fontWeight: 500
  }
}));

// Database selector styling
const DatabaseSelector = styled(Select)(({ theme }) => ({
  fontSize: '0.85rem',
  backgroundColor: 'rgba(30, 34, 48, 0.4)',
  borderRadius: theme.shape.borderRadius,
  '& .MuiSelect-select': {
    padding: '8px 32px 8px 12px',
  },
  '& .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: theme.palette.primary.main,
  }
}));

/**
 * ChatPanel Component
 * The central panel containing the chat interface and process steps
 * 
 * @param {Object} props
 * @param {function} props.onSubmitQuery - Callback for submitting a query
 * @param {Array} props.messages - Array of chat messages
 * @param {boolean} [props.loading=false] - Whether a query is processing
 * @param {Array} [props.processSteps=[]] - Process steps data
 * @param {Array} [props.agentPhases=[]] - Agent execution phases
 * @param {string} props.query - Current query text
 * @param {function} props.setQuery - Function to update query text
 * @param {Object} [props.activeConnection=null] - Currently active database connection
 * @param {Array} [props.connections=[]] - Available database connections
 * @param {function} [props.onConnectionSelect] - Callback when selecting a database connection
 * @param {function} [props.onNewSession] - Callback to start a new chat session
 * @param {Object} [props.sx] - Additional MUI styling
 */
const ChatPanel = ({ 
  onSubmitQuery,
  messages = [],
  loading = false,
  processSteps = [],
  agentPhases = [],
  query = '',
  setQuery,
  activeConnection = null,
  connections = [],
  onConnectionSelect,
  onNewSession,
  sx = {} 
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamPosition, setStreamPosition] = useState(0);
  const [dbSwitchMenuAnchor, setDbSwitchMenuAnchor] = useState(null);
  const messagesEndRef = useRef(null);
  
  // Track database context changes in the chat history
  const [databaseContextChanges, setDatabaseContextChanges] = useState([]);
  
  // Update database context changes when activeConnection changes
  useEffect(() => {
    if (activeConnection && (!databaseContextChanges.length || 
        databaseContextChanges[databaseContextChanges.length - 1].id !== activeConnection.id)) {
      setDatabaseContextChanges(prev => [...prev, { 
        id: activeConnection.id,
        database: activeConnection.database,
        type: activeConnection.type,
        timestamp: new Date().toISOString()
      }]);
    }
  }, [activeConnection]);
  
  // Auto scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, processSteps, agentPhases, streamPosition]);
  
  // Simulate streaming effect for agent phases when loading
  useEffect(() => {
    if (loading && agentPhases.length > 0) {
      const currentPhase = agentPhases[agentPhases.length - 1];
      if (currentPhase && currentPhase.content) {
        setIsStreaming(true);
        setStreamingContent(currentPhase.content);
        
        // Simulate typing effect
        let position = 0;
        const contentLength = currentPhase.content.length;
        const typingInterval = setInterval(() => {
          position += Math.floor(Math.random() * 5) + 1; // Random speed
          if (position >= contentLength) {
            position = contentLength;
            clearInterval(typingInterval);
            setIsStreaming(false);
          }
          setStreamPosition(position);
        }, 50);
        
        return () => clearInterval(typingInterval);
      }
    } else {
      setIsStreaming(false);
    }
  }, [loading, agentPhases]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !loading && activeConnection) {
      onSubmitQuery(query);
    }
  };
  
  const handleRecording = () => {
    setIsRecording(!isRecording);
    // TODO: Implement speech-to-text
  };
  
  const handleOpenDbSwitchMenu = (event) => {
    setDbSwitchMenuAnchor(event.currentTarget);
  };
  
  const handleCloseDbSwitchMenu = () => {
    setDbSwitchMenuAnchor(null);
  };
  
  const handleSwitchDatabase = (connectionId) => {
    if (onConnectionSelect && connectionId !== activeConnection?.id) {
      onConnectionSelect(connectionId);
    }
    handleCloseDbSwitchMenu();
  };

  // Find AI thinking message
  const aiThinkingMessage = messages.find(m => m.sender === 'ai' && m.isThinking);
  
  // Get database context for a specific message index
  const getDatabaseContextForMessage = (index) => {
    if (!databaseContextChanges.length) return null;
    
    // Find the latest database context change before this message
    for (let i = databaseContextChanges.length - 1; i >= 0; i--) {
      const contextChange = databaseContextChanges[i];
      // Check if this context applies to the message (simple approximation)
      if (i * 2 <= index) {
        return {
          database: contextChange.database,
          type: contextChange.type,
          id: contextChange.id
        };
      }
    }
    
    // Default to the first context if none matches
    return {
      database: databaseContextChanges[0].database,
      type: databaseContextChanges[0].type,
      id: databaseContextChanges[0].id
    };
  };

  return (
    <ChatContainer sx={sx}>
      {/* Chat Header with Database Context */}
      <Box 
        sx={{ 
          py: 1.5, 
          px: 2, 
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'rgba(18, 18, 18, 0.3)',
          backdropFilter: 'blur(8px)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DatabaseIcon color="primary" fontSize="small" />
          
          {activeConnection ? (
            <>
              <Typography variant="body2" fontWeight={500}>
                Connected to:
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" fontWeight={600} color="primary.main">
                  {activeConnection.database}
                </Typography>
                <Chip 
                  label={activeConnection.type} 
                  size="small"
                  sx={{ 
                    height: 20, 
                    fontSize: '0.7rem',
                    backgroundColor: 'rgba(24, 220, 255, 0.1)',
                    borderColor: 'rgba(24, 220, 255, 0.3)',
                    '& .MuiChip-label': { px: 1 }
                  }} 
                  variant="outlined"
                />
              </Box>
            </>
          ) : (
            <Typography variant="body2" fontWeight={500} color="text.secondary">
              Select a database to begin
            </Typography>
          )}
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {connections.length > 0 && (
            <>
              <Tooltip title="Switch Database">
                <Button 
                  size="small"
                  startIcon={<SwapHorizIcon />}
                  onClick={handleOpenDbSwitchMenu}
                  variant="outlined"
                  sx={{ 
                    fontSize: '0.75rem', 
                    py: 0.5,
                    backgroundColor: 'rgba(30, 34, 48, 0.4)',
                  }}
                >
                  Switch Database
                </Button>
              </Tooltip>
              <Menu
                anchorEl={dbSwitchMenuAnchor}
                open={Boolean(dbSwitchMenuAnchor)}
                onClose={handleCloseDbSwitchMenu}
                sx={{ 
                  '& .MuiPaper-root': {
                    backgroundColor: 'rgba(30, 34, 48, 0.95)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 1,
                    mt: 1
                  }
                }}
              >
                {connections.map(conn => (
                  <MenuItem
                    key={conn.id}
                    selected={activeConnection?.id === conn.id}
                    onClick={() => handleSwitchDatabase(conn.id)}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {conn.database}
                      </Typography>
                      <Chip 
                        label={conn.type} 
                        size="small"
                        sx={{ 
                          height: 18, 
                          fontSize: '0.65rem',
                          backgroundColor: 'rgba(24, 220, 255, 0.1)',
                          borderColor: 'rgba(24, 220, 255, 0.3)',
                        }} 
                        variant="outlined"
                      />
                    </Box>
                  </MenuItem>
                ))}
                
                {onNewSession && (
                  <>
                    <Divider sx={{ my: 1 }} />
                    <MenuItem onClick={onNewSession}>
                      <Typography variant="body2" color="primary.main">
                        + New Chat Session
                      </Typography>
                    </MenuItem>
                  </>
                )}
              </Menu>
            </>
          )}
        </Box>
      </Box>
      
      {/* Chat Messages */}
      <Box sx={{ 
        flexGrow: 1, 
        overflow: 'auto',
        p: 2,
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Welcome message if no messages yet */}
        {messages.length === 0 && (
          <GlassCard
            intensity="light"
            glow
            sx={{ 
              textAlign: 'center', 
              mt: 4,
              maxWidth: 600,
              mx: 'auto'
            }}
          >
            <Typography variant="h5" component="h2" sx={{ mb: 2, fontFamily: '"Space Grotesk", sans-serif' }}>
              <span className="gradient-text">Chat with your data</span>
            </Typography>
            <Typography sx={{ mb: 3 }}>
              {activeConnection 
                ? `Ask questions about your ${activeConnection.database} database in plain English.`
                : "Connect to a database to start asking questions in plain English."}
            </Typography>
            {activeConnection ? (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                <Button 
                  variant="outlined"
                  size="small"
                  onClick={() => setQuery("Show me all orders")}
                >
                  Show all orders
                </Button>
                <Button 
                  variant="outlined"
                  size="small"
                  onClick={() => setQuery("What were the top selling products?")}
                >
                  Top selling products
                </Button>
                <Button 
                  variant="outlined"
                  size="small"
                  onClick={() => setQuery("Find customers who haven't ordered in 3 months")}
                >
                  Inactive customers
                </Button>
              </Box>
            ) : (
              <>
                <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>
                  Please select a database to continue
                </Typography>
                
                {connections.length > 0 && (
                  <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
                    <DatabaseSelector
                      value={activeConnection?.id || ''}
                      onChange={(e) => onConnectionSelect && onConnectionSelect(e.target.value)}
                      displayEmpty
                      startAdornment={
                        <Box component="span" sx={{ display: 'flex', alignItems: 'center', mr: 1 }}>
                          <DatabaseIcon fontSize="small" sx={{ color: 'primary.main', mr: 0.5 }} />
                        </Box>
                      }
                      renderValue={(selected) => {
                        if (!selected) {
                          return <Typography variant="body2" color="text.secondary">Select Database</Typography>;
                        }
                        const conn = connections.find(c => c.id === selected);
                        return (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Typography variant="body2" noWrap>
                              {conn?.database || 'Unknown'} 
                            </Typography>
                            <Chip 
                              label={conn?.type || ''} 
                              size="small" 
                              sx={{ 
                                height: 18, 
                                fontSize: '0.65rem',
                                backgroundColor: 'rgba(24, 220, 255, 0.1)',
                                borderColor: 'rgba(24, 220, 255, 0.3)',
                              }} 
                              variant="outlined"
                            />
                          </Box>
                        );
                      }}
                    >
                      {connections.map((conn) => (
                        <MenuItem key={conn.id} value={conn.id}>
                          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                            <Typography variant="body2">{conn.database}</Typography>
                            <Typography variant="caption" color="text.secondary">{conn.type}</Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </DatabaseSelector>
                  </FormControl>
                )}
              </>
            )}
          </GlassCard>
        )}
        
        {/* Display database context change messages */}
        {databaseContextChanges.slice(0, -1).map((contextChange, index) => (
          <Box 
            key={`context-${index}`}
            component={motion.div}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            sx={{
              display: 'flex',
              justifyContent: 'center',
              my: 2,
              opacity: 0.8
            }}
          >
            <Box sx={{
              backgroundColor: 'rgba(30, 34, 48, 0.5)',
              backdropFilter: 'blur(8px)',
              borderRadius: 1,
              py: 0.75,
              px: 2,
              border: '1px dashed rgba(255, 255, 255, 0.1)'
            }}>
              <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DatabaseIcon fontSize="small" sx={{ fontSize: '0.9rem' }} />
                Switched context to <strong>{contextChange.database}</strong>
                <Chip 
                  label={contextChange.type} 
                  size="small"
                  sx={{ 
                    height: 16, 
                    fontSize: '0.65rem',
                    backgroundColor: 'rgba(24, 220, 255, 0.1)',
                    borderColor: 'rgba(24, 220, 255, 0.3)',
                    '& .MuiChip-label': { px: 0.5 }
                  }} 
                  variant="outlined"
                />
              </Typography>
            </Box>
          </Box>
        ))}
        
        {/* Display messages */}
        {messages.map((message, index) => {
          // Skip AI thinking messages as they'll be shown as agent phases
          if (message.sender === 'ai' && message.isThinking) return null;
          
          // Get database context for this message
          const dbContext = getDatabaseContextForMessage(index);
          const isSystemMessage = message.sender === 'system';
          
          return (
            <MessageContainer 
              key={index} 
              sender={message.sender}
              component={motion.div}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {/* Database context chip for non-system messages */}
              {dbContext && message.sender === 'user' && (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column',
                  alignItems: 'center',
                  mr: 1,
                  mt: 1
                }}>
                  <DatabaseChip 
                    label={dbContext.database}
                    size="small"
                    variant="outlined"
                    color="primary"
                  />
                </Box>
              )}
              
              <MessageContent sender={message.sender}>
                {/* System messages with result prefix */}
                {isSystemMessage && message.content.includes("Query executed successfully") ? (
                  <Typography>
                    <Box component="span" sx={{ fontWeight: 600, color: 'primary.main' }}>
                      [{dbContext?.database}]
                    </Box> {message.content}
                  </Typography>
                ) : message.content.startsWith('```') ? (
                  <CodeBlock
                    code={message.content.replace(/```(\w+)?\n([\s\S]*?)```/g, '$2')}
                    language="sql"
                  />
                ) : (
                  <Typography>{message.content}</Typography>
                )}
              </MessageContent>
              
              {/* Database context chip for AI messages */}
              {dbContext && message.sender === 'ai' && (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column',
                  alignItems: 'center',
                  ml: 1,
                  mt: 1
                }}>
                  <DatabaseChip 
                    label={dbContext.database}
                    size="small"
                    variant="outlined"
                    color="primary"
                  />
                </Box>
              )}
            </MessageContainer>
          );
        })}
        
        {/* Show agent phases if processing or if there are completed phases */}
        {(loading || agentPhases.length > 0) && (
          <Box 
            component={motion.div}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            sx={{ mt: 2, mb: 2 }}
          >
            <AgentPhasesDisplay 
              phases={agentPhases.map(phase => ({
                ...phase,
                // Keep the original phase status from backend
                // We only use 'in_progress' status for streaming the current phase
                isLiveStreaming: loading && phase.status === 'in_progress',
                streamPosition: isStreaming && phase.status === 'in_progress' ? streamPosition : null
              }))}
            />
          </Box>
        )}
        
        {/* Processing steps (legacy, can be removed if using agent phases) */}
        {loading && processSteps.length > 0 && !agentPhases.length && (
          <Box 
            component={motion.div}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            sx={{ mt: 2, mb: 2 }}
          >
            {processSteps.map((step, index) => (
              <ProcessStep
                key={index}
                title={step.title}
                status={step.status}
                expanded={index === processSteps.length - 1 && step.status === 'processing'}
              />
            ))}
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>
      
      {/* Input Area */}
      <InputContainer>
        <form onSubmit={handleSubmit} style={{ display: 'flex' }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder={activeConnection 
              ? `Ask a question about ${activeConnection.database}...` 
              : "Select a database to start..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading || !activeConnection}
            InputProps={{
              sx: {
                pr: 1,
                backgroundColor: 'rgba(0, 0, 0, 0.15)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                '&:hover': {
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                },
                '&.Mui-focused': {
                  border: '1px solid rgba(24, 220, 255, 0.5)',
                  boxShadow: '0 0 0 3px rgba(24, 220, 255, 0.2)',
                },
              }
            }}
          />
          <Box sx={{ display: 'flex', ml: 1 }}>
            <Tooltip title="Voice input">
              <IconButton
                color={isRecording ? 'error' : 'primary'}
                onClick={handleRecording}
                sx={{ mr: 1 }}
                disabled={!activeConnection}
              >
                <MicIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="contained"
              color="primary"
              type="submit"
              disabled={loading || !query.trim() || !activeConnection}
              sx={{ 
                minWidth: 0, 
                width: '48px', 
                height: '48px', 
                borderRadius: '50%',
                p: 0,
              }}
            >
              {loading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                <SendIcon />
              )}
            </Button>
          </Box>
        </form>
      </InputContainer>
    </ChatContainer>
  );
};

export default ChatPanel; 