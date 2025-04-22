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
 * @param {string} props.status - Status of the phase (processing, completed)
 * @param {boolean} props.isLiveStreaming - Whether content is currently being streamed
 * @param {number} props.streamPosition - Current position in the streaming content
 * @param {boolean} props.isLast - Whether this is the last phase
 */
const AgentPhaseDisplay = ({
  phase,
  content = '',
  status = 'processing',
  isLiveStreaming = false,
  streamPosition = 0,
  isLast = false
}) => {
  const [isExpanded, setIsExpanded] = useState(isLast);
  const [showFullContent, setShowFullContent] = useState(false);
  const contentRef = useRef(null);

  // Auto-expand current processing phase
  useEffect(() => {
    if (status === 'processing' && !isExpanded) {
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
    switch (phase) {
      case 'SCHEMA_ANALYSIS':
        return { 
          icon: <SchemaIcon />, 
          color: '#3BCBB0',
          title: 'Schema Analysis',
          description: 'Analyzing database schema to identify relevant tables and columns'
        };
      case 'PLAN_GENERATION':
        return { 
          icon: <AccountTreeIcon />, 
          color: '#18DCFF',
          title: 'Query Planning',
          description: 'Designing an execution plan for the query'
        };
      case 'CODE_GENERATION':
      case 'REFINEMENT_CODE_GENERATION':
        return { 
          icon: <CodeIcon />, 
          color: '#9D4EDD',
          title: 'Code Generation',
          description: 'Generating PySpark/SQL code based on the query plan'
        };
      case 'CODE_REVIEW':
        return { 
          icon: <BugReportIcon />, 
          color: '#FFC857',
          title: 'Code Review',
          description: 'Reviewing code for potential issues and optimizations'
        };
      case 'EXECUTION':
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
        return { 
          icon: <ContentPasteSearchIcon />, 
          color: '#7c7c7c',
          title: phase.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase()),
          description: 'Processing phase of query execution'
        };
    }
  };

  const { icon, color, title, description } = getPhaseDetails();

  // Determine if content should be collapsed
  const isContentLong = content.length > MAX_VISIBLE_CONTENT_LENGTH;
  const displayedContent = isLiveStreaming 
    ? content.substring(0, streamPosition) 
    : (showFullContent || !isContentLong) ? content : content.substring(0, MAX_VISIBLE_CONTENT_LENGTH) + '...';

  // Detect if content is code
  const isCode = content.trim().startsWith('```') || 
                 content.trim().startsWith('from ') || 
                 content.trim().startsWith('import ') ||
                 content.trim().startsWith('SELECT ') ||
                 content.trim().startsWith('def ') ||
                 content.trim().startsWith('{') ||
                 content.trim().startsWith('[');

  // Determine language for code highlighting
  const getLanguage = () => {
    if (content.includes('SELECT') || content.includes('FROM') || content.includes('WHERE')) return 'sql';
    if (content.includes('import ') || content.includes('def ')) return 'python';
    if (content.trim().startsWith('{') || content.trim().startsWith('[')) return 'json';
    return 'text';
  };

  return (
    <Box 
      sx={{
        border: '1px solid rgba(255, 255, 255, 0.05)',
        borderLeft: `3px solid ${color}`,
        borderRadius: 1,
        mb: 2,
        overflow: 'hidden',
        backgroundColor: isLast && status === 'processing' ? 'rgba(255, 255, 255, 0.03)' : 'transparent'
      }}
      component={motion.div}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
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
          <Box sx={{ color }}>
            {icon}
          </Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
            {title}
          </Typography>
          {status === 'processing' && (
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
          )}
          {status === 'completed' && (
            <CheckCircleIcon fontSize="small" sx={{ color: 'success.main', ml: 1 }} />
          )}
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

      {/* Collapsible Content */}
      <Collapse in={isExpanded}>
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
                sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}
              >
                {displayedContent}
              </Typography>
            )}
          </Box>
          
          {/* "Show more" button for long content */}
          {isContentLong && !isLiveStreaming && (
            <Box sx={{ textAlign: 'center', mt: 1 }}>
              <Typography
                variant="caption"
                sx={{
                  cursor: 'pointer',
                  color: 'primary.main',
                  '&:hover': { textDecoration: 'underline' }
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setShowFullContent(!showFullContent);
                }}
              >
                {showFullContent ? 'Show less' : 'Show more'}
              </Typography>
            </Box>
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

/**
 * AgentPhasesDisplay Component
 * Displays all agent execution phases in an organized, collapsible format
 * 
 * @param {Object} props
 * @param {Array} props.phases - Array of phase objects with name, content and status
 * @param {boolean} props.isStreaming - Whether agent is currently streaming output
 * @param {Object} props.streamingPhase - Currently streaming phase information
 */
const AgentPhasesDisplay = ({ 
  phases = [],
  isStreaming = false,
  streamingPhase = null,
  sx = {}
}) => {
  // Combine completed phases with currently streaming phase
  const allPhases = [...phases];
  
  if (isStreaming && streamingPhase && !phases.find(p => p.phase === streamingPhase.phase)) {
    allPhases.push(streamingPhase);
  }
  
  return (
    <Box sx={{ ...sx }}>
      {allPhases.map((phase, index) => (
        <AgentPhaseDisplay
          key={phase.phase}
          phase={phase.phase}
          content={phase.content}
          status={phase.status}
          isLiveStreaming={isStreaming && streamingPhase && streamingPhase.phase === phase.phase}
          streamPosition={streamingPhase ? streamingPhase.streamPosition : 0}
          isLast={index === allPhases.length - 1}
        />
      ))}
    </Box>
  );
};

export { AgentPhaseDisplay, AgentPhasesDisplay };
export default AgentPhasesDisplay; 