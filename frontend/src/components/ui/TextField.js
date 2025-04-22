import React from 'react';
import PropTypes from 'prop-types';
import { TextField as MuiTextField, InputAdornment, styled } from '@mui/material';

// Styled TextField component with enhanced customization
const StyledTextField = styled(MuiTextField)(({ 
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
  };

  return {
    '& .MuiOutlinedInput-root': {
      borderRadius: radiusMap[radius] || radiusMap.default,
      transition: 'all 0.2s ease-in-out',
      
      '&:hover .MuiOutlinedInput-notchedOutline': {
        borderColor: theme.palette.primary.main,
      },
      
      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
        borderWidth: '2px',
      },
    },
    
    '& .MuiInputLabel-root': {
      '&.Mui-focused': {
        color: theme.palette.primary.main,
      },
    },
    
    '& .MuiInputBase-input': {
      padding: size === 'small' 
        ? theme.spacing(1, 1.5) 
        : size === 'large' 
          ? theme.spacing(2, 2)
          : theme.spacing(1.5, 1.75),
      height: size === 'small' 
        ? '1rem' 
        : size === 'large' 
          ? '1.5rem'
          : '1.25rem',
    },
    
    '& .MuiFormHelperText-root': {
      marginLeft: theme.spacing(0.5),
      marginTop: theme.spacing(0.5),
    },
  };
});

/**
 * Custom TextField component with enhanced styling and functionality
 *
 * @param {Object} props - Component props
 * @param {string} props.label - Field label
 * @param {string} props.placeholder - Field placeholder
 * @param {string} props.defaultValue - Default value
 * @param {string} props.value - Controlled value
 * @param {function} props.onChange - Change handler function
 * @param {string} props.helperText - Helper text displayed below the field
 * @param {boolean} props.error - Whether the field has an error
 * @param {boolean} props.disabled - Whether the field is disabled
 * @param {boolean} props.required - Whether the field is required
 * @param {string} props.variant - Field variant (outlined, filled, standard)
 * @param {string} props.size - Field size (small, medium, large)
 * @param {string} props.radius - Border radius (none, small, default, medium, large)
 * @param {boolean} props.fullWidth - Whether the field takes full width
 * @param {string} props.type - Input type (text, password, number, email, etc.)
 * @param {ReactNode} props.startAdornment - Start adornment component
 * @param {ReactNode} props.endAdornment - End adornment component
 * @param {Object} props.inputProps - Props applied to the input element
 * @param {Object} props.InputProps - Props applied to the Input component
 * @param {string} props.id - Field id
 * @param {string} props.name - Field name
 * @param {boolean} props.multiline - Whether the field is multiline
 * @param {number} props.rows - Number of rows for multiline field
 * @param {number} props.maxRows - Maximum number of rows for multiline field
 * @param {boolean} props.autoFocus - Whether the field should be auto-focused
 * @param {string} props.className - Additional class names
 * @param {Object} props.sx - Additional styles
 * @returns {React.ReactElement} TextField component
 */
const TextField = ({
  label,
  placeholder,
  defaultValue,
  value,
  onChange,
  helperText,
  error = false,
  disabled = false,
  required = false,
  variant = 'outlined',
  size = 'medium',
  radius = 'default',
  fullWidth = true,
  type = 'text',
  startAdornment,
  endAdornment,
  inputProps = {},
  InputProps = {},
  id,
  name,
  multiline = false,
  rows,
  maxRows,
  autoFocus = false,
  className = '',
  sx = {},
  ...props
}) => {
  // Combine InputProps with adornments if provided
  const combinedInputProps = {
    ...InputProps,
    ...(startAdornment && {
      startAdornment: <InputAdornment position="start">{startAdornment}</InputAdornment>
    }),
    ...(endAdornment && {
      endAdornment: <InputAdornment position="end">{endAdornment}</InputAdornment>
    }),
  };

  return (
    <StyledTextField
      label={label}
      placeholder={placeholder}
      defaultValue={defaultValue}
      value={value}
      onChange={onChange}
      helperText={helperText}
      error={error}
      disabled={disabled}
      required={required}
      variant={variant}
      size={size === 'large' ? 'medium' : size} // MUI only supports 'small' and 'medium'
      radius={radius}
      fullWidth={fullWidth}
      type={type}
      InputProps={combinedInputProps}
      inputProps={inputProps}
      id={id}
      name={name}
      multiline={multiline}
      rows={rows}
      maxRows={maxRows}
      autoFocus={autoFocus}
      className={className}
      sx={sx}
      {...props}
    />
  );
};

TextField.propTypes = {
  label: PropTypes.string,
  placeholder: PropTypes.string,
  defaultValue: PropTypes.string,
  value: PropTypes.string,
  onChange: PropTypes.func,
  helperText: PropTypes.node,
  error: PropTypes.bool,
  disabled: PropTypes.bool,
  required: PropTypes.bool,
  variant: PropTypes.oneOf(['outlined', 'filled', 'standard']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  radius: PropTypes.oneOf(['none', 'small', 'default', 'medium', 'large']),
  fullWidth: PropTypes.bool,
  type: PropTypes.string,
  startAdornment: PropTypes.node,
  endAdornment: PropTypes.node,
  inputProps: PropTypes.object,
  InputProps: PropTypes.object,
  id: PropTypes.string,
  name: PropTypes.string,
  multiline: PropTypes.bool,
  rows: PropTypes.number,
  maxRows: PropTypes.number,
  autoFocus: PropTypes.bool,
  className: PropTypes.string,
  sx: PropTypes.object,
};

export default TextField; 