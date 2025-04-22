import React from 'react';
import PropTypes from 'prop-types';
import { Alert as MuiAlert, AlertTitle, Box, IconButton, Collapse, styled } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';

// Styled Alert component with enhanced customization
const StyledAlert = styled(MuiAlert)(({ 
  theme, 
  variant = 'standard',
  severity = 'info',
  borderPosition = 'left',
  isFilled = false,
  isGradient = false,
}) => {
  // Get the appropriate color from theme
  const getColor = (severity) => {
    const colorMap = {
      success: theme.palette.success,
      error: theme.palette.error,
      warning: theme.palette.warning,
      info: theme.palette.info,
    };
    
    return colorMap[severity] || colorMap.info;
  };
  
  const color = getColor(severity);
  
  // Base styles for all variants
  const baseStyles = {
    borderRadius: theme.shape.borderRadius,
    padding: theme.spacing(1, 2),
  };
  
  // Styles for standard variant
  const standardStyles = {
    backgroundColor: theme.palette.mode === 'dark' 
      ? `rgba(${theme.palette[severity].mainChannel} / 0.15)`
      : `rgba(${theme.palette[severity].mainChannel} / 0.1)`,
    color: theme.palette.mode === 'dark' 
      ? theme.palette[severity].light
      : theme.palette[severity].dark,
    
    '& .MuiAlert-icon': {
      color: theme.palette[severity].main,
    },
  };
  
  // Styles for outlined variant
  const outlinedStyles = {
    backgroundColor: 'transparent',
    border: `1px solid ${color.main}`,
    color: theme.palette.mode === 'dark' 
      ? color.light
      : color.dark,
    
    '& .MuiAlert-icon': {
      color: color.main,
    },
  };
  
  // Styles for filled variant
  const filledStyles = {
    backgroundColor: color.main,
    color: color.contrastText,
    boxShadow: theme.shadows[1],
    
    '& .MuiAlert-icon': {
      color: color.contrastText,
    },
  };
  
  // Border position styles
  const borderStyles = {
    left: {
      borderLeft: variant !== 'outlined' ? `3px solid ${color.main}` : undefined,
    },
    right: {
      borderRight: variant !== 'outlined' ? `3px solid ${color.main}` : undefined,
    },
    top: {
      borderTop: variant !== 'outlined' ? `3px solid ${color.main}` : undefined,
    },
    bottom: {
      borderBottom: variant !== 'outlined' ? `3px solid ${color.main}` : undefined,
    },
    none: {},
  };
  
  // Apply gradient background for filled variant with isGradient
  const gradientStyles = isGradient && (variant === 'filled' || isFilled) ? {
    background: `linear-gradient(90deg, ${color.main} 0%, ${color.light} 100%)`,
  } : {};
  
  // Get the variant styles
  const getVariantStyles = () => {
    if (variant === 'filled' || isFilled) return filledStyles;
    if (variant === 'outlined') return outlinedStyles;
    return standardStyles;
  };
  
  return {
    ...baseStyles,
    ...getVariantStyles(),
    ...borderStyles[borderPosition],
    ...gradientStyles,
    '& .MuiAlertTitle-root': {
      fontWeight: 600,
      marginBottom: theme.spacing(0.5),
    },
  };
});

/**
 * Enhanced Alert component with additional customization options
 *
 * @param {Object} props - Component props
 * @param {ReactNode} props.children - Alert content
 * @param {string} props.title - Alert title
 * @param {string} props.severity - Alert severity (success, error, warning, info)
 * @param {string} props.variant - Alert variant (standard, outlined, filled)
 * @param {string} props.borderPosition - Position of colored border (left, right, top, bottom, none)
 * @param {boolean} props.isFilled - Whether to use filled style regardless of variant
 * @param {boolean} props.isGradient - Whether to use gradient background for filled alerts
 * @param {boolean} props.onClose - Close handler function
 * @param {boolean} props.closeText - Text for the close button
 * @param {boolean} props.icon - Custom icon to display
 * @param {string} props.action - Additional action component
 * @param {boolean} props.square - Whether to use square corners
 * @param {boolean} props.elevation - Shadow elevation (0-24)
 * @param {Object} props.sx - Additional styles
 * @returns {React.ReactElement} Enhanced Alert component
 */
const Alert = ({
  children,
  title,
  severity = 'info',
  variant = 'standard',
  borderPosition = 'left',
  isFilled = false,
  isGradient = false,
  onClose,
  closeText,
  icon,
  action,
  square = false,
  elevation = 0,
  sx = {},
  ...props
}) => {
  // Custom default icons
  const getDefaultIcon = () => {
    switch (severity) {
      case 'success':
        return <CheckCircleIcon fontSize="inherit" />;
      case 'error':
        return <ErrorIcon fontSize="inherit" />;
      case 'warning':
        return <WarningIcon fontSize="inherit" />;
      default:
        return <InfoIcon fontSize="inherit" />;
    }
  };
  
  // Combine sx props
  const combinedSx = {
    ...sx,
    ...(square && { borderRadius: 0 }),
    ...(elevation > 0 && { boxShadow: (theme) => theme.shadows[elevation] }),
  };
  
  // Define the action element
  const actionElement = action || (onClose && (
    <IconButton
      size="small"
      aria-label={closeText || 'close'}
      color="inherit"
      onClick={onClose}
    >
      <CloseIcon fontSize="small" />
    </IconButton>
  ));

  return (
    <StyledAlert
      severity={severity}
      variant={variant}
      borderPosition={borderPosition}
      isFilled={isFilled}
      isGradient={isGradient}
      icon={icon !== undefined ? icon : getDefaultIcon()}
      action={actionElement}
      sx={combinedSx}
      {...props}
    >
      {title && <AlertTitle>{title}</AlertTitle>}
      {children}
    </StyledAlert>
  );
};

/**
 * AlertGroup component for displaying multiple alerts
 * 
 * @param {Object} props - Component props
 * @param {Array} props.alerts - Array of alert objects
 * @param {string} props.position - Stack direction (horizontal, vertical)
 * @param {number} props.spacing - Spacing between alerts
 * @param {Object} props.sx - Additional styles
 * @returns {React.ReactElement} AlertGroup component
 */
export const AlertGroup = ({
  alerts = [],
  position = 'vertical',
  spacing = 2,
  sx = {},
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: position === 'horizontal' ? 'row' : 'column',
        gap: spacing,
        width: '100%',
        ...sx
      }}
    >
      {alerts.map((alertProps, index) => (
        <Alert
          key={index}
          {...alertProps}
        />
      ))}
    </Box>
  );
};

/**
 * AlertWithCollapse component for alerts with expand/collapse functionality
 * 
 * @param {Object} props - Alert props
 * @param {boolean} props.open - Whether the alert is visible
 * @param {function} props.onClose - Close handler function
 * @param {Array} props.transitions - Animation duration
 * @returns {React.ReactElement} AlertWithCollapse component
 */
export const AlertWithCollapse = ({
  open = true,
  onClose,
  timeout = 300,
  ...alertProps
}) => {
  return (
    <Collapse in={open} timeout={timeout}>
      <Alert onClose={onClose} {...alertProps} />
    </Collapse>
  );
};

Alert.propTypes = {
  children: PropTypes.node,
  title: PropTypes.string,
  severity: PropTypes.oneOf(['success', 'error', 'warning', 'info']),
  variant: PropTypes.oneOf(['standard', 'outlined', 'filled']),
  borderPosition: PropTypes.oneOf(['left', 'right', 'top', 'bottom', 'none']),
  isFilled: PropTypes.bool,
  isGradient: PropTypes.bool,
  onClose: PropTypes.func,
  closeText: PropTypes.string,
  icon: PropTypes.node,
  action: PropTypes.node,
  square: PropTypes.bool,
  elevation: PropTypes.number,
  sx: PropTypes.object,
};

AlertGroup.propTypes = {
  alerts: PropTypes.array,
  position: PropTypes.oneOf(['horizontal', 'vertical']),
  spacing: PropTypes.number,
  sx: PropTypes.object,
};

AlertWithCollapse.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  timeout: PropTypes.number,
};

export default Alert; 