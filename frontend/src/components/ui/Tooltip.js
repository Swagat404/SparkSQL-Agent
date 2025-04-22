import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Tooltip as MuiTooltip, styled, Fade, Zoom } from '@mui/material';

// Styled Tooltip with enhanced customization options
const StyledTooltip = styled(({ className, ...props }) => (
  <MuiTooltip {...props} classes={{ popper: className }} />
))(({ 
  theme, 
  variant = 'default',
  size = 'medium',
  width,
  maxWidth = 220
}) => {
  // Size variants
  const sizeMap = {
    small: {
      fontSize: '0.75rem',
      padding: theme.spacing(0.5, 1),
    },
    medium: {
      fontSize: '0.8125rem',
      padding: theme.spacing(0.75, 1.25),
    },
    large: {
      fontSize: '0.875rem',
      padding: theme.spacing(1, 1.5),
    },
  };
  
  // Get size styles
  const sizeStyles = sizeMap[size] || sizeMap.medium;
  
  // Variant styles
  const variantStyles = {
    default: {
      backgroundColor: theme.palette.grey[800],
      color: theme.palette.common.white,
      boxShadow: theme.shadows[1],
    },
    light: {
      backgroundColor: theme.palette.common.white,
      color: theme.palette.text.primary,
      boxShadow: theme.shadows[2],
    },
    primary: {
      backgroundColor: theme.palette.primary.main,
      color: theme.palette.primary.contrastText,
      boxShadow: theme.shadows[1],
    },
    secondary: {
      backgroundColor: theme.palette.secondary.main,
      color: theme.palette.secondary.contrastText,
      boxShadow: theme.shadows[1],
    },
    error: {
      backgroundColor: theme.palette.error.main,
      color: theme.palette.error.contrastText,
      boxShadow: theme.shadows[1],
    },
    warning: {
      backgroundColor: theme.palette.warning.main,
      color: theme.palette.warning.contrastText,
      boxShadow: theme.shadows[1],
    },
    success: {
      backgroundColor: theme.palette.success.main,
      color: theme.palette.success.contrastText,
      boxShadow: theme.shadows[1],
    },
    info: {
      backgroundColor: theme.palette.info.main,
      color: theme.palette.info.contrastText,
      boxShadow: theme.shadows[1],
    },
    glass: {
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      color: theme.palette.common.white,
      boxShadow: theme.shadows[1],
    },
  };
  
  // Get variant styles
  const currentVariantStyles = variantStyles[variant] || variantStyles.default;

  return {
    '& .MuiTooltip-tooltip': {
      ...sizeStyles,
      ...currentVariantStyles,
      borderRadius: theme.shape.borderRadius,
      width: width || 'auto',
      maxWidth: maxWidth,
    },
    '& .MuiTooltip-arrow': {
      color: currentVariantStyles.backgroundColor,
    },
  };
});

/**
 * Enhanced Tooltip component with additional customization options
 *
 * @param {Object} props - Component props
 * @param {ReactNode} props.children - The element to apply the tooltip to
 * @param {ReactNode} props.title - Tooltip content
 * @param {string} props.variant - Tooltip variant (default, light, primary, secondary, error, warning, success, info, glass)
 * @param {string} props.size - Tooltip size (small, medium, large)
 * @param {number|string} props.width - Fixed width for tooltip (optional)
 * @param {number} props.maxWidth - Maximum width for tooltip
 * @param {string} props.placement - Tooltip placement
 * @param {string} props.arrow - Whether to show an arrow
 * @param {string} props.animation - Animation type (fade, zoom)
 * @param {number} props.enterDelay - Delay before tooltip appears (ms)
 * @param {number} props.leaveDelay - Delay before tooltip disappears (ms)
 * @param {boolean} props.followCursor - Whether tooltip should follow cursor
 * @param {boolean} props.interactive - Whether tooltip is interactive
 * @param {Object} props.sx - Additional styles
 * @returns {React.ReactElement} Enhanced Tooltip component
 */
const Tooltip = ({
  children,
  title,
  variant = 'default',
  size = 'medium',
  width,
  maxWidth = 220,
  placement = 'top',
  arrow = true,
  animation = 'fade',
  enterDelay = 100,
  leaveDelay = 0,
  followCursor = false,
  interactive = false,
  sx = {},
  ...props
}) => {
  const [open, setOpen] = useState(false);
  
  // Skip rendering if no title
  if (!title) {
    return children;
  }
  
  // Set animation component
  const getTransitionComponent = () => {
    if (animation === 'zoom') return Zoom;
    return Fade;
  };
  
  const TransitionComponent = getTransitionComponent();
  
  return (
    <StyledTooltip
      title={title}
      variant={variant}
      size={size}
      width={width}
      maxWidth={maxWidth}
      placement={placement}
      arrow={arrow}
      enterDelay={enterDelay}
      leaveDelay={leaveDelay}
      followCursor={followCursor}
      interactive={interactive}
      TransitionComponent={TransitionComponent}
      TransitionProps={{ timeout: 300 }}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      open={interactive ? open : undefined}
      sx={sx}
      {...props}
    >
      {/* Using a div wrapper when interactive to prevent focus issues */}
      {interactive ? <div>{children}</div> : children}
    </StyledTooltip>
  );
};

Tooltip.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.node,
  variant: PropTypes.oneOf(['default', 'light', 'primary', 'secondary', 'error', 'warning', 'success', 'info', 'glass']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  width: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  maxWidth: PropTypes.number,
  placement: PropTypes.oneOf([
    'top', 'top-start', 'top-end',
    'bottom', 'bottom-start', 'bottom-end',
    'left', 'left-start', 'left-end',
    'right', 'right-start', 'right-end'
  ]),
  arrow: PropTypes.bool,
  animation: PropTypes.oneOf(['fade', 'zoom']),
  enterDelay: PropTypes.number,
  leaveDelay: PropTypes.number,
  followCursor: PropTypes.bool,
  interactive: PropTypes.bool,
  sx: PropTypes.object,
};

export default Tooltip; 