import React from 'react';
import PropTypes from 'prop-types';
import { Box, styled, useTheme } from '@mui/material';

// Styled Badge component with customizable properties
const StyledBadge = styled(Box)(({
  theme,
  color = 'primary',
  variant = 'contained',
  size = 'medium',
  shape = 'rounded',
}) => {
  // Get the appropriate color from theme
  const getColor = () => {
    if (color in theme.palette) {
      return theme.palette[color];
    }
    return {
      main: color,
      contrastText: '#fff',
    };
  };

  const selectedColor = getColor();
  
  // Base styles
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    whiteSpace: 'nowrap',
    transition: theme.transitions.create(['background-color', 'box-shadow', 'border-color', 'color'], {
      duration: 200,
    }),
    fontWeight: 600,
  };
  
  // Size styles
  const sizeStyles = {
    small: {
      height: 20,
      fontSize: '0.65rem',
      padding: theme.spacing(0, 0.75),
    },
    medium: {
      height: 24,
      fontSize: '0.75rem',
      padding: theme.spacing(0, 1),
    },
    large: {
      height: 32,
      fontSize: '0.875rem',
      padding: theme.spacing(0, 1.5),
    },
  };
  
  // Shape styles
  const shapeStyles = {
    rounded: {
      borderRadius: theme.shape.borderRadius,
    },
    circular: {
      borderRadius: 100,
    },
    square: {
      borderRadius: 0,
    },
  };
  
  // Variant styles
  const variantStyles = {
    contained: {
      backgroundColor: selectedColor.main,
      color: selectedColor.contrastText,
    },
    outlined: {
      backgroundColor: 'transparent',
      border: `1px solid ${selectedColor.main}`,
      color: selectedColor.main,
    },
    soft: {
      backgroundColor: theme.palette.mode === 'dark' 
        ? `rgba(${theme.palette[color].mainChannel} / 0.17)`
        : `rgba(${theme.palette[color].mainChannel} / 0.12)`,
      color: selectedColor.main,
    },
    dot: {
      width: sizeStyles[size].height,
      height: sizeStyles[size].height,
      padding: 0,
      borderRadius: '50%',
      backgroundColor: selectedColor.main,
    },
  };

  return {
    ...baseStyles,
    ...sizeStyles[size],
    ...shapeStyles[shape],
    ...variantStyles[variant],
  };
});

/**
 * Badge component for displaying status, tags, and labels
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Badge content
 * @param {string} props.color - Badge color (theme color key or custom color)
 * @param {string} props.variant - Badge variant (contained, outlined, soft, dot)
 * @param {string} props.size - Badge size (small, medium, large)
 * @param {string} props.shape - Badge shape (rounded, circular, square)
 * @param {Object} props.sx - Additional styles
 * @returns {React.ReactElement} Badge component
 */
const Badge = ({
  children,
  color = 'primary',
  variant = 'contained',
  size = 'medium',
  shape = 'rounded',
  sx = {},
  ...props
}) => {
  const theme = useTheme();
  const isDot = variant === 'dot';

  return (
    <StyledBadge
      color={color}
      variant={variant}
      size={size}
      shape={isDot ? 'circular' : shape}
      sx={sx}
      {...props}
    >
      {!isDot && children}
    </StyledBadge>
  );
};

Badge.propTypes = {
  children: PropTypes.node,
  color: PropTypes.string,
  variant: PropTypes.oneOf(['contained', 'outlined', 'soft', 'dot']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  shape: PropTypes.oneOf(['rounded', 'circular', 'square']),
  sx: PropTypes.object,
};

export default Badge; 