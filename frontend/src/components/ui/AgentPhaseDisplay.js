import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, IconButton, Collapse, LinearProgress, Divider } from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CodeIcon from '@mui/icons-material/Code';
import SchemaIcon from '@mui/icons-material/Schema';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import BuildIcon from '@mui/icons-material/Build';
import BugReportIcon from '@mui/icons-material/BugReport';
import DoneAllIcon from '@mui/icons-material/DoneAll';
import ContentPasteSearchIcon from '@mui/icons-material/ContentPasteSearch';
import ErrorIcon from '@mui/icons-material/Error';
import { motion } from 'framer-motion';
import CodeBlock from './CodeBlock';

const MAX_VISIBLE_CONTENT_LENGTH = 500; // Characters before collapse

/**
 * AgentPhaseDisplay Component
 * Displays a single agent execution phase with collapsible content and live streaming effect
 * 
 * @param {Object} props
 * @param {string} props.phase - Phase name (e.g., SCHEMA_ANALYSIS, PLAN_GENERATION)
 * @param {string} props.content - The content of the phase
 * @param {string} props.status - Status of the phase (pending, in_progress, completed, failed)
 * @param {boolean} props.isLiveStreaming - Whether content is currently being streamed
 * @param {number} props.streamPosition - Current position in the streaming content
 * @param {boolean} props.isLast - Whether this is the last phase
 */
const AgentPhaseDisplay = ({
  phase,
  content = '',
  status = 'pending',
  isLiveStreaming = false,
  streamPosition = 0,
  isLast = false
}) => {
  const [isExpanded, setIsExpanded] = useState(status === 'in_progress');
  const [showFullContent, setShowFullContent] = useState(false);
  const contentRef = useRef(null);

  // Auto-expand current processing phase
  useEffect(() => {
    if (status === 'in_progress' && !isExpanded) {
      setIsExpanded(true);
    }
  }, [status, isExpanded]);

  // Auto-scroll to the bottom of the content during live streaming
  useEffect(() => {
    if (isLiveStreaming && contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [isLiveStreaming, streamPosition]);

  // Determine phase icon and color
  const getPhaseDetails = () => {
    // Safety check for undefined phase
    if (!phase) {
      return { 
        icon: <ContentPasteSearchIcon />, 
        color: '#7c7c7c',
        title: 'Unknown Phase',
        description: 'Processing query'
      };
    }
    
    switch (phase) {
      case 'SCHEMA_ANALYSIS':
      case 'schema_analysis':
        return { 
          icon: <SchemaIcon />, 
          color: '#3BCBB0',
          title: 'Schema Analysis',
          description: 'Analyzing database schema to identify relevant tables and columns'
        };
      case 'PLAN_GENERATION':
      case 'query_planning':
        return { 
          icon: <AccountTreeIcon />, 
          color: '#18DCFF',
          title: 'Query Planning',
          description: 'Designing an execution plan for the query'
        };
      case 'CODE_GENERATION':
      case 'code_generation':
      case 'REFINEMENT_CODE_GENERATION':
        return { 
          icon: <CodeIcon />, 
          color: '#9D4EDD',
          title: 'Code Generation',
          description: 'Generating PySpark/SQL code based on the query plan'
        };
      case 'CODE_REVIEW':
      case 'code_review':
        return { 
          icon: <BugReportIcon />, 
          color: '#FFC857',
          title: 'Code Review',
          description: 'Reviewing code for potential issues and optimizations'
        };
      case 'EXECUTION':
      case 'executing_query':
        return { 
          icon: <BuildIcon />, 
          color: '#FF5A5A',
          title: 'Execution',
          description: 'Executing the generated code against the database'
        };
      case 'FINAL_CODE':
        return { 
          icon: <DoneAllIcon />, 
          color: '#4CAF50',
          title: 'Final Code',
          description: 'The optimized, final code to be executed'
        };
      default:
        // Safe replacement that checks if phase exists and is a string
        const phaseStr = typeof phase === 'string' ? phase : 'unknown';
        return { 
          icon: <ContentPasteSearchIcon />, 
          color: '#7c7c7c',
          title: phaseStr.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase()),
          description: 'Processing phase of query execution'
        };
    }
  };

  const { icon, color, title, description } = getPhaseDetails();

  // Determine if content should be collapsed
  const isContentLong = content && content.length > MAX_VISIBLE_CONTENT_LENGTH;
  const displayedContent = isLiveStreaming 
    ? content.substring(0, streamPosition) 
    : (showFullContent || !isContentLong) ? content : content.substring(0, MAX_VISIBLE_CONTENT_LENGTH) + '...';

  // Detect if content is code
  const isCode = content && (
    content.trim().startsWith('```') || 
    content.trim().startsWith('from ') || 
    content.trim().startsWith('import ') ||
    content.trim().startsWith('SELECT ') ||
    content.trim().startsWith('def ') ||
    content.trim().startsWith('{') ||
    content.trim().startsWith('[')
  );

  // Determine language for code highlighting
  const getLanguage = () => {
    if (!content) return 'text';
    if (content.includes('SELECT') || content.includes('FROM') || content.includes('WHERE')) return 'sql';
    if (content.includes('import ') || content.includes('def ')) return 'python';
    if (content.trim().startsWith('{') || content.trim().startsWith('[')) return 'json';
    return 'text';
  };

  // Get status styles
  const getStatusStyles = () => {
    switch (status) {
      case 'completed':
        return {
          border: '1px solid rgba(255, 255, 255, 0.05)',
          borderLeft: `3px solid ${color}`,
          opacity: 1
        };
      case 'in_progress':
        return {
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderLeft: `3px solid ${color}`,
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          opacity: 1
        };
      case 'failed':
        return {
          border: '1px solid rgba(255, 99, 71, 0.3)',
          borderLeft: '3px solid #FF6347',
          opacity: 1
        };
      case 'pending':
      default:
        return {
          border: '1px solid rgba(255, 255, 255, 0.03)',
          borderLeft: `3px solid rgba(124, 124, 124, 0.5)`,
          opacity: 0.6
        };
    }
  };

  // Get status indicator
  const renderStatusIndicator = () => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon fontSize="small" sx={{ color: 'success.main', ml: 1 }} />;
      case 'in_progress':
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
            <LinearProgress 
              sx={{ 
                width: 60,
                height: 4,
                borderRadius: 1,
                '& .MuiLinearProgress-bar': {
                  background: `linear-gradient(90deg, ${color} 0%, rgba(255, 255, 255, 0.3) 100%)`,
                }
              }} 
            />
          </Box>
        );
      case 'failed':
        return <ErrorIcon fontSize="small" sx={{ color: 'error.main', ml: 1 }} />;
      case 'pending':
      default:
        return null;
    }
  };

  return (
    <Box 
      sx={{
        ...getStatusStyles(),
        borderRadius: 1,
        mb: 2,
        overflow: 'hidden',
      }}
      component={motion.div}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: status === 'pending' ? 0.6 : 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <Box 
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 1.5,
          cursor: 'pointer',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
          },
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ color: status === 'pending' ? 'rgba(124, 124, 124, 0.7)' : color }}>
            {icon}
          </Box>
          <Typography 
            variant="subtitle1" 
            sx={{ 
              fontWeight: 500,
              color: status === 'pending' ? 'text.disabled' : 'text.primary'
            }}
          >
            {title}
          </Typography>
          {renderStatusIndicator()}
        </Box>
        <IconButton 
          size="small" 
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
          disabled={status === 'pending' && !content}
        >
          {isExpanded ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
        </IconButton>
      </Box>

      {/* Collapsible Content */}
      <Collapse in={isExpanded}>
        {content ? (
          <Box 
            sx={{ 
              p: 2, 
              pt: 0, 
              borderTop: '1px solid rgba(255, 255, 255, 0.05)',
              backgroundColor: 'rgba(0, 0, 0, 0.2)'
            }}
          >
            <Typography variant="body2" sx={{ mb: 1.5, color: 'text.secondary' }}>
              {description}
            </Typography>
            
            <Divider sx={{ mb: 2, opacity: 0.2 }} />
            
            <Box 
              ref={contentRef}
              sx={{ 
                maxHeight: isContentLong && !showFullContent ? '300px' : 'none',
                overflow: isContentLong && !showFullContent ? 'auto' : 'visible',
                position: 'relative'
              }}
            >
              {isCode ? (
                <CodeBlock 
                  code={displayedContent.replace(/```(\w+)?\n?([\s\S]*?)```/g, '$2')} 
                  language={getLanguage()}
                  showLineNumbers
                />
              ) : (
                <Typography 
                  variant="body2" 
                  component="div"
                  sx={{ 
                    fontFamily: 'monospace', 
                    whiteSpace: 'pre-wrap',
                    fontSize: '0.9rem',
                    lineHeight: 1.6
                  }}
                >
                  {displayedContent}
                </Typography>
              )}
            </Box>
            
            {/* Show toggle if content is long */}
            {isContentLong && (
              <Box 
                sx={{ 
                  mt: 2,
                  display: 'flex',
                  justifyContent: 'center'
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    cursor: 'pointer',
                    color: 'primary.main',
                    textDecoration: 'underline'
                  }}
                  onClick={() => setShowFullContent(!showFullContent)}
                >
                  {showFullContent ? 'Show Less' : 'Show Full Content'}
                </Typography>
              </Box>
            )}
          </Box>
        ) : (
          <Box 
            sx={{ 
              p: 2,
              borderTop: '1px solid rgba(255, 255, 255, 0.05)',
              backgroundColor: 'rgba(0, 0, 0, 0.2)',
              textAlign: 'center'
            }}
          >
            <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
              {status === 'pending' ? 'Waiting to start...' : 'No content available for this phase'}
            </Typography>
          </Box>
        )}
      </Collapse>
    </Box>
  );
};

/**
 * AgentPhasesDisplay Component
 * Displays a collection of agent execution phases
 * 
 * @param {Object} props
 * @param {Array} props.phases - Array of phases to display
 * @param {boolean} props.isStreaming - Whether content is currently being streamed
 * @param {Object} props.streamingPhase - Information about the current streaming phase
 * @param {Object} props.sx - Additional styling
 */
const AgentPhasesDisplay = ({ 
  phases = [],
  isStreaming = false,
  streamingPhase = null,
  sx = {}
}) => {
  // Safety check for phases array
  if (!Array.isArray(phases)) {
    console.error('Invalid phases prop:', phases);
    return (
      <Box sx={{ ...sx }}>
        <Typography variant="body2" color="text.secondary" align="center">
          No agent phases to display
        </Typography>
      </Box>
    );
  }

  // Organize phases by attempt number
  const phasesByAttempt = {};
  let maxAttempt = 1;
  
  phases.forEach(phase => {
    const attemptNum = phase.attempt || 1;
    if (!phasesByAttempt[attemptNum]) {
      phasesByAttempt[attemptNum] = [];
    }
    
    // Keep track of max attempt
    if (attemptNum > maxAttempt) {
      maxAttempt = attemptNum;
    }
    
    // Ensure phase has all required properties with defaults if missing
    phasesByAttempt[attemptNum].push({
      phase: phase.id || 'unknown',
      content: phase.thinking || '',
      status: phase.status || 'completed',
      title: phase.name || 'Unknown Phase',
      isRetryIndicator: phase.is_retry_indicator || false
    });
  });

  return (
    <Box sx={{ ...sx }}>
      {Object.keys(phasesByAttempt).length === 0 ? (
        <Typography variant="body2" color="text.secondary" align="center">
          No agent phases to display
        </Typography>
      ) : (
        // Display each attempt, starting from the earliest
        Object.keys(phasesByAttempt)
          .map(Number)
          .sort((a, b) => a - b)
          .map(attemptNum => (
            <Box key={`attempt-${attemptNum}`}>
              {/* Show attempt number if there were multiple attempts */}
              {maxAttempt > 1 && (
                <Box 
                  sx={{ 
                    mt: 3, 
                    mb: 2, 
                    display: 'flex', 
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Divider sx={{ flexGrow: 1, opacity: 0.3 }} />
                  <Box
                    sx={{
                      mx: 2,
                      px: 2,
                      py: 0.75,
                      borderRadius: 1,
                      backgroundColor: 'rgba(0, 0, 0, 0.15)',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <Typography variant="subtitle2" color="primary.main">
                      {attemptNum === maxAttempt 
                        ? `Final Attempt (${attemptNum})`
                        : `Attempt ${attemptNum}`}
                    </Typography>
                  </Box>
                  <Divider sx={{ flexGrow: 1, opacity: 0.3 }} />
                </Box>
              )}
              
              {/* Display phases for this attempt */}
              {phasesByAttempt[attemptNum].map((phase, index) => (
                <React.Fragment key={`${phase.phase}-${index}`}>
                  {phase.isRetryIndicator ? (
                    <Box
                      sx={{
                        p: 1.5,
                        mb: 2,
                        borderRadius: 1,
                        backgroundColor: 'rgba(255, 99, 71, 0.1)',
                        border: '1px solid rgba(255, 99, 71, 0.3)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 1
                      }}
                    >
                      <ErrorIcon color="error" fontSize="small" />
                      <Typography variant="body2" color="error.main">
                        {phase.title} 
                      </Typography>
                    </Box>
                  ) : (
                    <AgentPhaseDisplay
                      phase={phase.phase}
                      content={phase.content}
                      status={phase.status}
                      isLiveStreaming={isStreaming && streamingPhase && streamingPhase.phase === phase.phase}
                      streamPosition={isStreaming && streamingPhase && streamingPhase.phase === phase.phase ? streamingPhase.streamPosition : 0}
                      isLast={attemptNum === maxAttempt && index === phasesByAttempt[attemptNum].length - 1}
                    />
                  )}
                </React.Fragment>
              ))}
            </Box>
          ))
      )}
    </Box>
  );
};

export { AgentPhaseDisplay };
export default AgentPhasesDisplay; 