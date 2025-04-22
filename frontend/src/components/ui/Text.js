import React from 'react';
import PropTypes from 'prop-types';
import { Typography, styled } from '@mui/material';

// Styled Typography component with enhanced customization
const StyledTypography = styled(Typography)(({ 
  theme, 
  textTransform,
  noWrap,
  truncate,
  maxLines,
  highlight,
  highlightColor = 'primary',
  letterSpacing
}) => ({
  textTransform: textTransform || 'none',
  whiteSpace: noWrap ? 'nowrap' : 'normal',
  overflow: (noWrap || truncate || maxLines) ? 'hidden' : 'visible',
  textOverflow: (noWrap || truncate) ? 'ellipsis' : 'clip',
  letterSpacing: letterSpacing,
  
  // Handle max lines with line clamp
  ...(maxLines && {
    display: '-webkit-box',
    WebkitLineClamp: maxLines,
    WebkitBoxOrient: 'vertical',
  }),
  
  // Handle text highlighting
  ...(highlight && {
    backgroundColor: theme.palette[highlightColor]?.light || theme.palette.primary.light,
    color: theme.palette[highlightColor]?.contrastText || theme.palette.primary.contrastText,
    padding: '0 4px',
    borderRadius: '2px',
  })
}));

/**
 * Enhanced Typography component with additional text formatting options
 *
 * @param {Object} props - Component props
 * @param {ReactNode} props.children - Text content
 * @param {string} props.variant - Typography variant (h1, h2, h3, h4, h5, h6, subtitle1, subtitle2, body1, body2, caption, overline, etc.)
 * @param {string} props.component - HTML element to render (h1, h2, p, span, div, etc.)
 * @param {string} props.color - Text color (primary, secondary, textPrimary, textSecondary, error, etc.)
 * @param {string} props.align - Text alignment (left, center, right, justify)
 * @param {string} props.weight - Font weight (light, regular, medium, bold)
 * @param {string} props.fontStyle - Font style (normal, italic)
 * @param {string} props.textTransform - Text transformation (none, capitalize, uppercase, lowercase)
 * @param {boolean} props.noWrap - Whether text should be truncated with ellipsis when it overflows
 * @param {boolean} props.truncate - Whether text should be truncated with ellipsis (alternative to noWrap)
 * @param {number} props.maxLines - Maximum number of lines before truncating with ellipsis
 * @param {boolean} props.gutterBottom - Whether text should have margin bottom
 * @param {boolean} props.highlight - Whether text should be highlighted
 * @param {string} props.highlightColor - Highlight color (primary, secondary, error, etc.)
 * @param {string} props.letterSpacing - Letter spacing
 * @param {string} props.className - Additional class names
 * @param {Object} props.sx - Additional styles
 * @returns {React.ReactElement} Enhanced Typography component
 */
const Text = ({
  children,
  variant = 'body1',
  component,
  color = 'text.primary',
  align = 'inherit',
  weight,
  fontStyle,
  textTransform,
  noWrap = false,
  truncate = false,
  maxLines,
  gutterBottom = false,
  highlight = false,
  highlightColor = 'primary',
  letterSpacing,
  className = '',
  sx = {},
  ...props
}) => {
  // Handle font weight through sx prop
  const fontWeightMap = {
    light: 300,
    regular: 400,
    medium: 500,
    bold: 700,
  };
  
  const fontWeightValue = weight ? fontWeightMap[weight] || weight : undefined;
  
  const combinedSx = {
    ...(fontWeightValue && { fontWeight: fontWeightValue }),
    ...(fontStyle && { fontStyle }),
    ...sx,
  };
  
  return (
    <StyledTypography
      variant={variant}
      component={component}
      color={color}
      align={align}
      gutterBottom={gutterBottom}
      noWrap={noWrap}
      truncate={truncate}
      maxLines={maxLines}
      highlight={highlight}
      highlightColor={highlightColor}
      textTransform={textTransform}
      letterSpacing={letterSpacing}
      className={className}
      sx={combinedSx}
      {...props}
    >
      {children}
    </StyledTypography>
  );
};

Text.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.string,
  component: PropTypes.string,
  color: PropTypes.string,
  align: PropTypes.oneOf(['inherit', 'left', 'center', 'right', 'justify']),
  weight: PropTypes.oneOfType([
    PropTypes.oneOf(['light', 'regular', 'medium', 'bold']),
    PropTypes.number
  ]),
  fontStyle: PropTypes.oneOf(['normal', 'italic']),
  textTransform: PropTypes.oneOf(['none', 'capitalize', 'uppercase', 'lowercase']),
  noWrap: PropTypes.bool,
  truncate: PropTypes.bool,
  maxLines: PropTypes.number,
  gutterBottom: PropTypes.bool,
  highlight: PropTypes.bool,
  highlightColor: PropTypes.string,
  letterSpacing: PropTypes.string,
  className: PropTypes.string,
  sx: PropTypes.object,
};

export default Text; 