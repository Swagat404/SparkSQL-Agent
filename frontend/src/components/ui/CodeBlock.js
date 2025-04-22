import React, { useState } from 'react';
import { Box, IconButton, Tooltip, Typography } from '@mui/material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';

// Custom dark theme for code blocks
const codeTheme = {
  ...atomDark,
  'pre[class*="language-"]': {
    ...atomDark['pre[class*="language-"]'],
    background: 'rgba(13, 15, 24, 0.6)',
    margin: 0,
    borderRadius: '6px',
    padding: '12px 16px',
  },
  'code[class*="language-"]': {
    ...atomDark['code[class*="language-"]'],
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: '0.875rem',
  },
  comment: {
    ...atomDark.comment,
    color: '#607B96',
  },
  function: {
    ...atomDark.function,
    color: '#18DCFF',
  },
  string: {
    ...atomDark.string,
    color: '#3BCBB0',
  },
  keyword: {
    ...atomDark.keyword,
    color: '#9D4EDD',
  },
};

/**
 * CodeBlock Component
 * A syntax-highlighted code block with copy functionality
 * 
 * @param {Object} props
 * @param {string} props.code - The code to display
 * @param {string} [props.language='sql'] - The programming language
 * @param {string} [props.title] - Optional title for the code block
 * @param {Object} [props.sx] - Additional MUI styling
 */
const CodeBlock = ({ 
  code = '', 
  language = 'sql', 
  title,
  sx = {} 
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Box 
      sx={{ 
        position: 'relative',
        borderRadius: 1,
        overflow: 'hidden',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        mb: 2,
        ...sx 
      }}
    >
      {title && (
        <Box 
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 2,
            py: 1,
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
            background: 'rgba(30, 34, 48, 0.6)',
          }}
        >
          <Typography variant="body2" fontFamily="'JetBrains Mono', monospace" color="text.secondary">
            {title}
          </Typography>
          <Tooltip title={copied ? 'Copied!' : 'Copy code'}>
            <IconButton size="small" onClick={handleCopy} color={copied ? 'success' : 'default'}>
              {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
        </Box>
      )}
      <Box sx={{ position: 'relative' }}>
        {!title && (
          <Tooltip title={copied ? 'Copied!' : 'Copy code'}>
            <IconButton 
              size="small" 
              onClick={handleCopy} 
              color={copied ? 'success' : 'default'}
              sx={{ 
                position: 'absolute', 
                top: 8, 
                right: 8, 
                backgroundColor: 'rgba(18, 22, 32, 0.6)',
                '&:hover': {
                  backgroundColor: 'rgba(18, 22, 32, 0.8)',
                }
              }}
            >
              {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
        )}
        <SyntaxHighlighter
          language={language}
          style={codeTheme}
          wrapLines={true}
          showLineNumbers={true}
        >
          {code}
        </SyntaxHighlighter>
      </Box>
    </Box>
  );
};

export default CodeBlock; 