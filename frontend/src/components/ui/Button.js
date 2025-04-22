import React from 'react';
import PropTypes from 'prop-types';
import { Button as MuiButton, styled, CircularProgress } from '@mui/material';

// Styled Button with enhanced customization options
const StyledButton = styled(MuiButton)(({ 
  theme, 
  size, 
  rounded, 
  fullWidth, 
  elevation, 
  hoverElevation,
  textTransform,
  iconPosition
}) => ({
  textTransform: textTransform || 'none',
  boxShadow: elevation ? theme.shadows[elevation] : 'none',
  minWidth: size === 'icon' ? 'auto' : undefined,
  width: fullWidth ? '100%' : undefined,
  borderRadius: rounded ? '50px' : undefined,
  padding: size === 'icon' ? '8px' : undefined,
  
  ...(iconPosition === 'left' && {
    '& .MuiButton-startIcon': {
      marginRight: theme.spacing(1),
    }
  }),
  
  ...(iconPosition === 'right' && {
    '& .MuiButton-endIcon': {
      marginLeft: theme.spacing(1),
    }
  }),
  
  '&:hover': {
    boxShadow: hoverElevation ? theme.shadows[hoverElevation] : undefined,
  },
  
  '&.Mui-disabled': {
    opacity: 0.6,
  }
}));

/**
 * Enhanced Button component with additional customization options
 *
 * @param {Object} props - Component props
 * @param {ReactNode} props.children - Button content
 * @param {ReactNode} props.startIcon - Icon to display before the button label
 * @param {ReactNode} props.endIcon - Icon to display after the button label
 * @param {string} props.variant - Button variant (text, outlined, contained, soft)
 * @param {string} props.color - Button color (primary, secondary, success, error, info, warning)
 * @param {string} props.size - Button size (small, medium, large, icon)
 * @param {boolean} props.fullWidth - Whether button should take full width
 * @param {boolean} props.rounded - Whether button should have rounded corners
 * @param {number} props.elevation - Shadow elevation (0-24)
 * @param {number} props.hoverElevation - Shadow elevation on hover (0-24)
 * @param {string} props.textTransform - Text transformation (none, capitalize, uppercase, lowercase)
 * @param {boolean} props.loading - Whether button is in loading state
 * @param {string} props.iconPosition - Position of the icon (left, right)
 * @param {string} props.component - Component to render as (button, a, div, etc.)
 * @param {string} props.href - URL if button is a link
 * @param {string} props.target - Target if button is a link
 * @param {boolean} props.disabled - Whether button is disabled
 * @param {function} props.onClick - Click handler
 * @returns {React.ReactElement} Enhanced Button component
 */
const Button = ({
  children,
  startIcon,
  endIcon,
  variant = 'contained',
  color = 'primary',
  size = 'medium',
  fullWidth = false,
  rounded = false,
  elevation = variant === 'contained' ? 1 : 0,
  hoverElevation = variant === 'contained' ? 2 : 0,
  textTransform = 'none',
  loading = false,
  iconPosition = 'left',
  component = 'button',
  href,
  target,
  disabled = false,
  onClick,
  sx = {},
  ...props
}) => {
  // Convert 'soft' variant to contained with custom styling
  const buttonVariant = variant === 'soft' ? 'contained' : variant;
  const buttonColor = variant === 'soft' ? 'inherit' : color;
  
  // Calculate actual icon placement based on iconPosition
  const buttonStartIcon = iconPosition === 'left' ? startIcon : null;
  const buttonEndIcon = iconPosition === 'right' ? endIcon : null;
  
  // Create combined sx for soft variant
  const combinedSx = {
    ...(variant === 'soft' && {
      backgroundColor: `${color}.light`,
      color: `${color}.main`,
      '&:hover': {
        backgroundColor: `${color}.main`,
        color: `${color}.contrastText`,
      },
    }),
    ...sx,
  };

  return (
    <StyledButton
      variant={buttonVariant}
      color={buttonColor}
      size={size === 'icon' ? 'medium' : size}
      fullWidth={fullWidth}
      rounded={rounded}
      elevation={elevation}
      hoverElevation={hoverElevation}
      textTransform={textTransform}
      iconPosition={iconPosition}
      component={component}
      href={href}
      target={target}
      disabled={disabled || loading}
      onClick={onClick}
      startIcon={buttonStartIcon && !loading ? buttonStartIcon : loading && iconPosition === 'left' ? <CircularProgress size={20} color="inherit" /> : null}
      endIcon={buttonEndIcon && !loading ? buttonEndIcon : loading && iconPosition === 'right' ? <CircularProgress size={20} color="inherit" /> : null}
      sx={combinedSx}
      {...props}
    >
      {loading && !buttonStartIcon && !buttonEndIcon ? (
        <>
          <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
          {children}
        </>
      ) : children}
    </StyledButton>
  );
};

Button.propTypes = {
  children: PropTypes.node,
  startIcon: PropTypes.node,
  endIcon: PropTypes.node,
  variant: PropTypes.oneOf(['text', 'outlined', 'contained', 'soft']),
  color: PropTypes.oneOf(['primary', 'secondary', 'success', 'error', 'info', 'warning', 'inherit']),
  size: PropTypes.oneOf(['small', 'medium', 'large', 'icon']),
  fullWidth: PropTypes.bool,
  rounded: PropTypes.bool,
  elevation: PropTypes.number,
  hoverElevation: PropTypes.number,
  textTransform: PropTypes.oneOf(['none', 'capitalize', 'uppercase', 'lowercase']),
  loading: PropTypes.bool,
  iconPosition: PropTypes.oneOf(['left', 'right']),
  component: PropTypes.elementType,
  href: PropTypes.string,
  target: PropTypes.string,
  disabled: PropTypes.bool,
  onClick: PropTypes.func,
  sx: PropTypes.object,
};

export default Button; 