import React from 'react';
import PropTypes from 'prop-types';
import { Box, Paper } from '@mui/material';
import { styled } from '@mui/material/styles';

// Styled container for the gradient border effect
const GradientBorderContainer = styled(Box)(({ 
  theme, 
  borderWidth = 1,
  gradientType = 'border',
  borderRadius = 16,
  gradientDirection = 'to right'
}) => ({
  position: 'relative',
  padding: gradientType === 'border' ? borderWidth : 0,
  borderRadius,
  background: `linear-gradient(${gradientDirection}, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
  display: 'inline-flex',
  width: '100%',
}));

// Styled content container
const ContentContainer = styled(Paper)(({ 
  theme, 
  gradientType,
  borderRadius = 16,
  elevation = 1,
  backgroundOpacity = 0.8
}) => ({
  position: 'relative',
  zIndex: 1,
  borderRadius: gradientType === 'border' ? borderRadius - 2 : borderRadius,
  padding: theme.spacing(3),
  background: gradientType === 'background' 
    ? `linear-gradient(135deg, ${theme.palette.background.paper} ${backgroundOpacity * 100}%, transparent)` 
    : theme.palette.background.paper,
  width: '100%',
  height: '100%',
  boxShadow: elevation > 0 ? theme.shadows[elevation] : 'none',
}));

// Styled gradient overlay for background type
const GradientOverlay = styled(Box)(({
  theme,
  gradientDirection = 'to right',
  opacity = 0.1
}) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  borderRadius: 'inherit',
  background: `linear-gradient(${gradientDirection}, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
  opacity,
  zIndex: 0,
}));

/**
 * GradientCard Component
 * A card component with customizable gradient styling
 * 
 * @param {Object} props
 * @param {ReactNode} props.children - Card content
 * @param {string} props.gradientType - Gradient type (border, background, full)
 * @param {string} props.gradientDirection - Direction of gradient
 * @param {number} props.borderWidth - Width of border in pixels (for border type)
 * @param {number} props.borderRadius - Border radius in pixels
 * @param {number} props.elevation - Shadow elevation (0-24)
 * @param {number} props.backgroundOpacity - Background opacity (0-1) for background type
 * @param {number} props.gradientOpacity - Gradient opacity (0-1) for background type
 * @param {Object} props.sx - Additional style props
 */
const GradientCard = ({ 
  children,
  gradientType = 'border',
  gradientDirection = 'to right',
  borderWidth = 2,
  borderRadius = 16,
  elevation = 1,
  backgroundOpacity = 0.8,
  gradientOpacity = 0.1,
  sx = {},
  ...props 
}) => {
  // For full gradient, use background type with lower background opacity
  const effectiveGradientType = gradientType === 'full' ? 'background' : gradientType;
  const effectiveBackgroundOpacity = gradientType === 'full' ? 0.4 : backgroundOpacity;

  if (gradientType === 'background' || gradientType === 'full') {
    return (
      <Box
        sx={{
          position: 'relative',
          borderRadius,
          width: '100%',
          overflow: 'hidden',
          ...sx
        }}
        {...props}
      >
        <GradientOverlay 
          gradientDirection={gradientDirection}
          opacity={gradientOpacity}
        />
        <ContentContainer
          gradientType={effectiveGradientType}
          borderRadius={borderRadius}
          elevation={elevation}
          backgroundOpacity={effectiveBackgroundOpacity}
        >
          {children}
        </ContentContainer>
      </Box>
    );
  }

  return (
    <GradientBorderContainer
      borderWidth={borderWidth}
      gradientType={gradientType}
      borderRadius={borderRadius}
      gradientDirection={gradientDirection}
      sx={sx}
      {...props}
    >
      <ContentContainer
        gradientType={gradientType}
        borderRadius={borderRadius}
        elevation={elevation}
      >
        {children}
      </ContentContainer>
    </GradientBorderContainer>
  );
};

GradientCard.propTypes = {
  children: PropTypes.node,
  gradientType: PropTypes.oneOf(['border', 'background', 'full']),
  gradientDirection: PropTypes.string,
  borderWidth: PropTypes.number,
  borderRadius: PropTypes.number,
  elevation: PropTypes.number,
  backgroundOpacity: PropTypes.number,
  gradientOpacity: PropTypes.number,
  sx: PropTypes.object,
};

export default GradientCard; 