import React from 'react';
import { Box, Paper } from '@mui/material';
import { styled } from '@mui/material/styles';

// The styled API from @mui/material/styles doesn't support transient props with $
// We need to handle this differently
const GlassContainer = styled(Paper)(({ theme, intensity = 0.1, glow }) => ({
  background: `rgba(255, 255, 255, ${intensity})`,
  backdropFilter: 'blur(10px)',
  borderRadius: 16,
  padding: theme.spacing(4),
  boxShadow: glow 
    ? '0 8px 32px rgba(0, 0, 0, 0.1), 0 0 40px rgba(128, 107, 230, 0.1)' 
    : '0 8px 32px rgba(0, 0, 0, 0.1)',
  border: '1px solid rgba(255, 255, 255, 0.18)',
  position: 'relative',
  overflow: 'hidden',
}));

const TopRightGlow = styled(Box)({
  position: 'absolute',
  top: '-80px',
  right: '-80px',
  width: '150px',
  height: '150px',
  background: 'radial-gradient(circle, rgba(58, 134, 255, 0.15) 0%, rgba(58, 134, 255, 0) 70%)',
  borderRadius: '100%',
});

const BottomLeftGlow = styled(Box)({
  position: 'absolute',
  bottom: '-80px',
  left: '-80px',
  width: '150px',
  height: '150px',
  background: 'radial-gradient(circle, rgba(157, 78, 221, 0.15) 0%, rgba(157, 78, 221, 0) 70%)',
  borderRadius: '100%',
});

/**
 * A glassy card component with frosted glass effect
 * 
 * @param {Object} props
 * @param {number} [props.intensity=0.1] - Intensity of the glass effect (0-1)
 * @param {boolean} [props.glow=false] - Whether to add a subtle glow effect
 * @param {React.ReactNode} props.children - Card content
 * @param {Object} [props.sx] - Additional style props
 */
const GlassCard = ({ children, intensity = 0.1, glow = false, sx = {}, ...props }) => {
  // Filter out the glow prop so it doesn't get passed to the DOM
  const { glow: _, ...otherProps } = props;
  
  // Use custom prop to avoid passing glow to DOM
  const containerProps = {
    intensity,
    glow,
    elevation: 0,
    sx,
    ...otherProps
  };

  return (
    <GlassContainer 
      {...containerProps}
    >
      {glow && (
        <>
          <TopRightGlow />
          <BottomLeftGlow />
        </>
      )}
      {children}
    </GlassContainer>
  );
};

export default GlassCard; 