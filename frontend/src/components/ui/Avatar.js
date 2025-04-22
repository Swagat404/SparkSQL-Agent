import React from 'react';
import PropTypes from 'prop-types';
import { Avatar as MuiAvatar, styled, Box } from '@mui/material';

// Styled Avatar with enhanced customization options
const StyledAvatar = styled(MuiAvatar)(({ 
  theme, 
  size, 
  variant = 'circular',
  bordered = false,
  borderColor = 'primary',
  borderWidth = 2,
  outline = false,
  outlineColor = 'primary',
  outlineWidth = 2,
  outlineOffset = 2
}) => {
  // Size variants
  const sizeMap = {
    xs: 24,
    sm: 32,
    md: 40,
    lg: 56,
    xl: 72,
  };
  
  // Get the actual size in pixels
  const pixelSize = typeof size === 'number' ? size : sizeMap[size] || sizeMap.md;
  
  // Get the color from theme or use the provided string
  const getBorderColor = () => {
    if (borderColor in theme.palette) {
      return theme.palette[borderColor].main;
    }
    return borderColor;
  };
  
  const getOutlineColor = () => {
    if (outlineColor in theme.palette) {
      return theme.palette[outlineColor].main;
    }
    return outlineColor;
  };
  
  return {
    width: pixelSize,
    height: pixelSize,
    fontSize: pixelSize * 0.4,
    fontWeight: 600,
    
    ...(variant === 'rounded' && {
      borderRadius: theme.shape.borderRadius,
    }),
    
    ...(variant === 'square' && {
      borderRadius: 0,
    }),
    
    ...(bordered && {
      border: `${borderWidth}px solid ${getBorderColor()}`,
    }),
    
    ...(outline && {
      boxShadow: `0 0 0 ${outlineWidth}px ${getOutlineColor()}`,
      margin: outlineOffset + outlineWidth,
    }),
  };
});

// Styled container for status indicator
const StatusContainer = styled(Box)(({ theme, size }) => {
  // Size variants
  const sizeMap = {
    xs: 24,
    sm: 32,
    md: 40,
    lg: 56,
    xl: 72,
  };
  
  // Get the actual size in pixels
  const pixelSize = typeof size === 'number' ? size : sizeMap[size] || sizeMap.md;
  
  // Calculate status indicator size based on avatar size
  const statusSize = Math.max(8, pixelSize * 0.25);
  
  return {
    position: 'relative',
    display: 'inline-flex',
    
    '& .status-indicator': {
      position: 'absolute',
      bottom: 0,
      right: 0,
      width: statusSize,
      height: statusSize,
      borderRadius: '50%',
      border: `2px solid ${theme.palette.background.paper}`,
      zIndex: 1,
    },
  };
});

/**
 * Enhanced Avatar component with additional customization options
 *
 * @param {Object} props - Component props
 * @param {string} props.alt - Text used for alt attribute and fallback
 * @param {string} props.src - Image URL
 * @param {React.ReactNode} props.children - Avatar content (usually text or icon)
 * @param {string|number} props.size - Avatar size (xs, sm, md, lg, xl or number in pixels)
 * @param {string} props.variant - Avatar shape (circular, rounded, square)
 * @param {boolean} props.bordered - Whether avatar should have a border
 * @param {string} props.borderColor - Border color (theme color or CSS color)
 * @param {number} props.borderWidth - Border width in pixels
 * @param {boolean} props.outline - Whether avatar should have an outline
 * @param {string} props.outlineColor - Outline color (theme color or CSS color)
 * @param {number} props.outlineWidth - Outline width in pixels
 * @param {number} props.outlineOffset - Outline offset in pixels
 * @param {string} props.status - Status indicator (online, offline, away, busy)
 * @param {string} props.statusColor - Custom status color (overrides status)
 * @param {Object} props.sx - Additional styles
 * @returns {React.ReactElement} Enhanced Avatar component
 */
const Avatar = ({
  alt,
  src,
  children,
  size = 'md',
  variant = 'circular',
  bordered = false,
  borderColor = 'primary',
  borderWidth = 2,
  outline = false,
  outlineColor = 'primary',
  outlineWidth = 2,
  outlineOffset = 2,
  status = null,
  statusColor = null,
  sx = {},
  ...props
}) => {
  // Status color mapping
  const statusColorMap = {
    online: 'success.main',
    offline: 'text.disabled',
    away: 'warning.main',
    busy: 'error.main',
  };
  
  // Get status color
  const getStatusColor = () => {
    if (statusColor) return statusColor;
    return status && statusColorMap[status] ? statusColorMap[status] : null;
  };
  
  const finalStatusColor = getStatusColor();
  
  // If status is provided, wrap in status container
  if (finalStatusColor) {
    return (
      <StatusContainer size={size}>
        <StyledAvatar
          alt={alt}
          src={src}
          size={size}
          variant={variant}
          bordered={bordered}
          borderColor={borderColor}
          borderWidth={borderWidth}
          outline={outline}
          outlineColor={outlineColor}
          outlineWidth={outlineWidth}
          outlineOffset={outlineOffset}
          sx={sx}
          {...props}
        >
          {children}
        </StyledAvatar>
        <Box 
          className="status-indicator" 
          sx={{ bgcolor: finalStatusColor }}
        />
      </StatusContainer>
    );
  }
  
  // Without status indicator
  return (
    <StyledAvatar
      alt={alt}
      src={src}
      size={size}
      variant={variant}
      bordered={bordered}
      borderColor={borderColor}
      borderWidth={borderWidth}
      outline={outline}
      outlineColor={outlineColor}
      outlineWidth={outlineWidth}
      outlineOffset={outlineOffset}
      sx={sx}
      {...props}
    >
      {children}
    </StyledAvatar>
  );
};

Avatar.propTypes = {
  alt: PropTypes.string,
  src: PropTypes.string,
  children: PropTypes.node,
  size: PropTypes.oneOfType([
    PropTypes.oneOf(['xs', 'sm', 'md', 'lg', 'xl']),
    PropTypes.number
  ]),
  variant: PropTypes.oneOf(['circular', 'rounded', 'square']),
  bordered: PropTypes.bool,
  borderColor: PropTypes.string,
  borderWidth: PropTypes.number,
  outline: PropTypes.bool,
  outlineColor: PropTypes.string,
  outlineWidth: PropTypes.number,
  outlineOffset: PropTypes.number,
  status: PropTypes.oneOf(['online', 'offline', 'away', 'busy', null]),
  statusColor: PropTypes.string,
  sx: PropTypes.object,
};

export default Avatar; 