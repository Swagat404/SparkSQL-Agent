import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  IconButton, 
  CircularProgress,
  Tooltip,
  Divider
} from '@mui/material';
import { styled } from '@mui/material/styles';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import SettingsIcon from '@mui/icons-material/Settings';
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
  sx = {} 
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamPosition, setStreamPosition] = useState(0);
  const messagesEndRef = useRef(null);
  
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
    if (query.trim() && !loading) {
      onSubmitQuery(query);
    }
  };
  
  const handleRecording = () => {
    setIsRecording(!isRecording);
    // TODO: Implement speech-to-text
  };

  // Find AI thinking message
  const aiThinkingMessage = messages.find(m => m.sender === 'ai' && m.isThinking);

  // Example process steps data based on attached compiler log
  const exampleSteps = [
    {
      title: "Schema Analysis",
      status: "completed",
      explanation: "Analyzing the database schema to identify relevant tables and columns for the query.",
      code: `{
  "tables": ["orders", "customers"],
  "columns": {
    "orders": ["order_id", "customer_id", "order_date", "total_amount"],
    "customers": ["customer_id", "name", "email"]
  },
  "joins": [
    {
      "left_table": "orders",
      "left_column": "customer_id",
      "right_table": "customers",
      "right_column": "customer_id"
    }
  ],
  "explanation": "To fulfill the request 'give me all orders', the primary table needed is 'orders'..."
}`,
      language: "json"
    },
    {
      title: "Query Planning",
      status: "completed",
      explanation: "Designing an execution plan for transforming the data using PySpark.",
      code: `### Execution Plan

1. **Load the Necessary Tables:**
   - Load the \`orders\` table into a DataFrame called \`orders_df\`.
   - Load the \`customers\` table into a DataFrame called \`customers_df\`.

2. **Select Relevant Columns:**
   - From \`orders_df\`, select the columns: \`order_id\`, \`customer_id\`, \`order_date\`, and \`total_amount\`.
   - From \`customers_df\`, select the columns: \`customer_id\`, \`name\`, and \`email\`.

3. **Perform the Join Operation:**
   - Join \`orders_df\` with \`customers_df\` on the \`customer_id\` column.`,
      language: "markdown"
    },
    {
      title: "Code Generation",
      status: "completed",
      explanation: "Generating PySpark code to execute the planned query.",
      code: `# Necessary imports
from pyspark.sql import SparkSession

# JDBC connection details
jdbc_url = "jdbc:postgresql://localhost:5432/postgres"
connection_properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

# Load the orders table into a DataFrame
orders_df = spark.read.jdbc(url=jdbc_url, table="orders", properties=connection_properties)

# Select relevant columns from the orders DataFrame
all_orders_df = orders_df.select(
    orders_df["order_id"],
    orders_df["customer_id"],
    orders_df["order_date"],
    orders_df["total_amount"]
)

# Display all orders
all_orders_df.show()`,
      language: "python"
    },
    {
      title: "Execution",
      status: "completed",
      explanation: "Executing the generated code against the database.",
      code: ``
    }
  ];

  return (
    <ChatContainer sx={sx}>
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
              Ask questions in plain English or write SQL queries to analyze your data.
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
              <Button 
                variant="outlined"
                size="small"
                onClick={() => setQuery("Show me all orders")}
              >
                Show me all orders
              </Button>
              <Button 
                variant="outlined"
                size="small"
                onClick={() => setQuery("What are the top 5 customers by total purchase amount?")}
              >
                Top 5 customers
              </Button>
              <Button 
                variant="outlined"
                size="small"
                onClick={() => setQuery("SELECT * FROM orders LIMIT 10")}
              >
                SELECT * FROM orders
              </Button>
            </Box>
          </GlassCard>
        )}
        
        {/* Display messages */}
        {messages.map((message, index) => {
          // Skip AI thinking messages as they'll be shown as agent phases
          if (message.sender === 'ai' && message.isThinking) return null;
          
          return (
            <MessageContainer 
              key={index} 
              sender={message.sender}
              component={motion.div}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <MessageContent sender={message.sender}>
                {message.content.startsWith('```') ? (
                  <CodeBlock
                    code={message.content.replace(/```(\w+)?\n([\s\S]*?)```/g, '$2')}
                    language="sql"
                  />
                ) : (
                  <Typography>{message.content}</Typography>
                )}
              </MessageContent>
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
                status: loading && phase === agentPhases[agentPhases.length - 1] 
                  ? 'processing' 
                  : 'completed'
              }))}
              isStreaming={isStreaming}
              streamingPhase={isStreaming ? {
                phase: agentPhases[agentPhases.length - 1].phase,
                streamPosition: streamPosition
              } : null}
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
            placeholder="Enter SQL query or ask a question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
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
              >
                <MicIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="contained"
              color="primary"
              type="submit"
              disabled={loading || !query.trim()}
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