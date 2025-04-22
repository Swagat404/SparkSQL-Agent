import React from 'react';
import PropTypes from 'prop-types';
import { Card as MuiCard, CardContent, CardActions, CardHeader, CardMedia, styled, Typography } from '@mui/material';

// Styled Card with enhanced customization
const StyledCard = styled(MuiCard)(({ 
  theme, 
  elevation = 1,
  radius = 'default',
  padding = 'medium',
  hoverEffect = false,
  bordered = false,
  borderColor = 'divider'
}) => {
  // Border radius variants
  const radiusMap = {
    none: '0px',
    small: `${theme.shape.borderRadius / 2}px`,
    default: `${theme.shape.borderRadius}px`,
    medium: `${theme.shape.borderRadius * 1.5}px`,
    large: `${theme.shape.borderRadius * 2}px`,
  };

  // Padding variants
  const paddingMap = {
    none: 0,
    small: theme.spacing(1),
    medium: theme.spacing(2),
    large: theme.spacing(3),
  };

  return {
    borderRadius: radiusMap[radius] || radiusMap.default,
    boxShadow: elevation ? theme.shadows[elevation] : 'none',
    transition: 'all 0.2s ease-in-out',
    border: bordered ? `1px solid ${theme.palette[borderColor]?.main || theme.palette.divider}` : 'none',
    
    ...(hoverEffect && {
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: theme.shadows[elevation + 1],
      }
    }),
    
    '& .MuiCardContent-root': {
      padding: paddingMap[padding],
      '&:last-child': {
        paddingBottom: paddingMap[padding],
      }
    },
    
    '& .MuiCardActions-root': {
      padding: padding === 'none' ? 0 : `0 ${paddingMap[padding]}px ${paddingMap[padding]}px`,
    },
    
    '& .MuiCardHeader-root': {
      padding: padding === 'none' ? 0 : paddingMap[padding],
    }
  };
});

// Styled CardContent for custom padding
const StyledCardContent = styled(CardContent)(({ theme, padding = 'medium' }) => {
  const paddingMap = {
    none: 0,
    small: theme.spacing(1),
    medium: theme.spacing(2),
    large: theme.spacing(3),
  };
  
  return {
    padding: paddingMap[padding] || paddingMap.medium,
    '&:last-child': {
      paddingBottom: paddingMap[padding] || paddingMap.medium,
    }
  };
});

/**
 * Custom Card component with enhanced styling and functionality
 *
 * @param {Object} props - Component props
 * @param {ReactNode} props.children - Card content
 * @param {number} props.elevation - Card elevation (0-24)
 * @param {string} props.radius - Border radius (none, small, default, medium, large)
 * @param {string} props.padding - Card padding (none, small, medium, large)
 * @param {boolean} props.hoverEffect - Whether to show hover effect
 * @param {boolean} props.bordered - Whether to show border
 * @param {string} props.borderColor - Border color (primary, secondary, error, etc. or divider)
 * @param {Object} props.title - Title config {text, variant, component, align, color}
 * @param {Object} props.subtitle - Subtitle config {text, variant, component, align, color}
 * @param {ReactNode} props.header - Custom header component
 * @param {ReactNode} props.media - Media config {component, height, image, title, alt}
 * @param {ReactNode} props.actions - Actions component(s) to display at bottom
 * @param {string} props.className - Additional class names
 * @param {Object} props.sx - Additional styles
 * @returns {React.ReactElement} Card component
 */
const Card = ({
  children,
  elevation = 1,
  radius = 'default',
  padding = 'medium',
  hoverEffect = false,
  bordered = false,
  borderColor = 'divider',
  title = null,
  subtitle = null,
  header = null,
  media = null,
  actions = null,
  className = '',
  sx = {},
  ...props
}) => {
  // Process title config
  const renderTitle = () => {
    if (typeof title === 'string') {
      return <Typography variant="h6" component="h2">{title}</Typography>;
    } else if (title && typeof title === 'object') {
      const { text, variant = 'h6', component = 'h2', align = 'inherit', color = 'text.primary' } = title;
      return <Typography variant={variant} component={component} align={align} color={color}>{text}</Typography>;
    }
    return null;
  };

  // Process subtitle config
  const renderSubtitle = () => {
    if (typeof subtitle === 'string') {
      return <Typography variant="body2" color="text.secondary">{subtitle}</Typography>;
    } else if (subtitle && typeof subtitle === 'object') {
      const { text, variant = 'body2', component = 'p', align = 'inherit', color = 'text.secondary' } = subtitle;
      return <Typography variant={variant} component={component} align={align} color={color}>{text}</Typography>;
    }
    return null;
  };

  // Generate header from title/subtitle if no custom header provided
  const cardHeader = header || ((title || subtitle) ? (
    <CardHeader
      title={renderTitle()}
      subheader={renderSubtitle()}
      disableTypography
    />
  ) : null);

  // Process media config
  const cardMedia = media && (
    <CardMedia
      component={media.component || 'img'}
      height={media.height}
      image={media.image}
      title={media.title}
      alt={media.alt || media.title}
    />
  );

  // Process actions
  const cardActions = actions && (
    <CardActions disableSpacing={actions.disableSpacing !== false}>
      {actions.children || actions}
    </CardActions>
  );

  return (
    <StyledCard
      elevation={elevation}
      radius={radius}
      padding={padding}
      hoverEffect={hoverEffect}
      bordered={bordered}
      borderColor={borderColor}
      className={className}
      sx={sx}
      {...props}
    >
      {cardHeader}
      {cardMedia}
      {children && <StyledCardContent padding={padding}>{children}</StyledCardContent>}
      {cardActions}
    </StyledCard>
  );
};

Card.propTypes = {
  children: PropTypes.node,
  elevation: PropTypes.number,
  radius: PropTypes.oneOf(['none', 'small', 'default', 'medium', 'large']),
  padding: PropTypes.oneOf(['none', 'small', 'medium', 'large']),
  hoverEffect: PropTypes.bool,
  bordered: PropTypes.bool,
  borderColor: PropTypes.string,
  title: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.shape({
      text: PropTypes.string.isRequired,
      variant: PropTypes.string,
      component: PropTypes.string,
      align: PropTypes.string,
      color: PropTypes.string,
    })
  ]),
  subtitle: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.shape({
      text: PropTypes.string.isRequired,
      variant: PropTypes.string,
      component: PropTypes.string,
      align: PropTypes.string,
      color: PropTypes.string,
    })
  ]),
  header: PropTypes.node,
  media: PropTypes.shape({
    component: PropTypes.string,
    height: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
    image: PropTypes.string.isRequired,
    title: PropTypes.string,
    alt: PropTypes.string,
  }),
  actions: PropTypes.oneOfType([
    PropTypes.node,
    PropTypes.shape({
      children: PropTypes.node,
      disableSpacing: PropTypes.bool,
    })
  ]),
  className: PropTypes.string,
  sx: PropTypes.object,
};

export default Card; 