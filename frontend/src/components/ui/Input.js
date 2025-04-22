import React, { forwardRef } from 'react';
import PropTypes from 'prop-types';
import { 
  TextField, 
  InputAdornment,
  FormHelperText,
  FormControl,
  InputLabel,
  styled
} from '@mui/material';

// Styled TextField component with enhanced customization
const StyledTextField = styled(TextField)(({ 
  theme, 
  size = 'medium',
  radius = 'default',
  fullWidth = true,
  variant = 'outlined',
}) => {
  // Border radius variants
  const radiusMap = {
    none: '0px',
    small: `${theme.shape.borderRadius / 2}px`,
    default: `${theme.shape.borderRadius}px`,
    medium: `${theme.shape.borderRadius * 1.5}px`,
    large: `${theme.shape.borderRadius * 2}px`,
    rounded: '20px',
  };

  const borderRadius = radiusMap[radius] || radiusMap.default;

  return {
    width: fullWidth ? '100%' : 'auto',
    
    '& .MuiOutlinedInput-root': {
      borderRadius,
      ...(size === 'small' && { 
        fontSize: '0.875rem',
      }),
      ...(size === 'large' && { 
        fontSize: '1.125rem',
      }),
    },
    
    '& .MuiInputLabel-root': {
      ...(size === 'small' && { 
        fontSize: '0.875rem',
        transform: 'translate(14px, 12px) scale(1)',
        '&.MuiInputLabel-shrink': {
          transform: 'translate(14px, -6px) scale(0.75)',
        },
      }),
      
      ...(size === 'large' && { 
        fontSize: '1.125rem',
        transform: 'translate(14px, 20px) scale(1)',
        '&.MuiInputLabel-shrink': {
          transform: 'translate(14px, -6px) scale(0.75)',
        },
      }),
    },
    
    '& .MuiInputBase-inputSizeSmall': {
      padding: theme.spacing(1, 1.5),
    },
    
    '& .MuiInputBase-inputSizeMedium': {
      padding: theme.spacing(1.5, 2),
    },
    
    '& .MuiInputBase-inputSizeLarge': {
      padding: theme.spacing(2, 2.5),
    },
  };
});

/**
 * Custom Input component with enhanced styling options
 * 
 * @param {Object} props - Component props
 * @param {string} props.id - Input id
 * @param {string} props.name - Input name
 * @param {string} props.label - Input label
 * @param {string} props.placeholder - Input placeholder
 * @param {string} props.helperText - Helper text displayed below the input
 * @param {string} props.error - Error message
 * @param {boolean} props.disabled - Whether input is disabled
 * @param {boolean} props.required - Whether input is required
 * @param {string} props.size - Input size (small, medium, large)
 * @param {string} props.radius - Border radius (none, small, default, medium, large, rounded)
 * @param {string} props.variant - Input variant (outlined, filled, standard)
 * @param {boolean} props.fullWidth - Whether input takes full width
 * @param {React.ReactNode} props.startAdornment - Element to display before input
 * @param {React.ReactNode} props.endAdornment - Element to display after input
 * @param {string} props.type - Input type (text, password, email, etc.)
 * @param {string} props.value - Input value
 * @param {function} props.onChange - Change handler
 * @param {function} props.onBlur - Blur handler
 * @param {function} props.onFocus - Focus handler
 * @param {Object} props.sx - Additional styles
 * @param {Object} props.InputProps - Props applied to the Input element
 * @param {Object} props.inputProps - Props applied to the input element
 * @returns {React.ReactElement} Input component
 */
const Input = forwardRef(({
  id,
  name,
  label,
  placeholder,
  helperText,
  error,
  disabled = false,
  required = false,
  size = 'medium',
  radius = 'default',
  variant = 'outlined',
  fullWidth = true,
  startAdornment,
  endAdornment,
  type = 'text',
  value,
  onChange,
  onBlur,
  onFocus,
  sx = {},
  InputProps = {},
  inputProps = {},
  ...props
}, ref) => {
  // Prepare input props with adornments
  const inputPropsWithAdornments = {
    ...InputProps,
    ...(startAdornment && {
      startAdornment: (
        <InputAdornment position="start">
          {startAdornment}
        </InputAdornment>
      )
    }),
    ...(endAdornment && {
      endAdornment: (
        <InputAdornment position="end">
          {endAdornment}
        </InputAdornment>
      )
    }),
  };
  
  // Set input size for Material-UI
  const muiSize = size === 'large' ? 'medium' : size;

  return (
    <FormControl 
      fullWidth={fullWidth} 
      error={!!error}
      disabled={disabled}
      sx={sx}
    >
      <StyledTextField
        id={id}
        name={name}
        label={label}
        placeholder={placeholder}
        size={muiSize}
        radius={radius}
        variant={variant}
        fullWidth={fullWidth}
        type={type}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        onFocus={onFocus}
        error={!!error}
        disabled={disabled}
        required={required}
        InputProps={inputPropsWithAdornments}
        inputProps={inputProps}
        inputRef={ref}
        {...props}
      />
      {(helperText || error) && (
        <FormHelperText error={!!error}>
          {error || helperText}
        </FormHelperText>
      )}
    </FormControl>
  );
});

Input.displayName = 'Input';

Input.propTypes = {
  id: PropTypes.string,
  name: PropTypes.string,
  label: PropTypes.string,
  placeholder: PropTypes.string,
  helperText: PropTypes.string,
  error: PropTypes.string,
  disabled: PropTypes.bool,
  required: PropTypes.bool,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  radius: PropTypes.oneOf(['none', 'small', 'default', 'medium', 'large', 'rounded']),
  variant: PropTypes.oneOf(['outlined', 'filled', 'standard']),
  fullWidth: PropTypes.bool,
  startAdornment: PropTypes.node,
  endAdornment: PropTypes.node,
  type: PropTypes.string,
  value: PropTypes.any,
  onChange: PropTypes.func,
  onBlur: PropTypes.func,
  onFocus: PropTypes.func,
  sx: PropTypes.object,
  InputProps: PropTypes.object,
  inputProps: PropTypes.object,
};

export default Input; 