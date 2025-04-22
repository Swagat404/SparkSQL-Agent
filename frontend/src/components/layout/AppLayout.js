import React, { useState } from 'react';
import { Box, IconButton, useMediaQuery, useTheme } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * AppLayout Component
 * A three-panel layout with responsive behavior
 * 
 * @param {Object} props
 * @param {ReactNode} props.leftSidebar - Content for the left sidebar
 * @param {ReactNode} props.center - Content for the center panel
 * @param {ReactNode} props.rightPanel - Content for the right panel
 * @param {Object} [props.sx] - Additional MUI styling
 */
const AppLayout = ({ leftSidebar, center, rightPanel, sx = {} }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.down('lg'));
  
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(!isMobile);
  const [rightPanelOpen, setRightPanelOpen] = useState(!isTablet);
  
  // Calculate panel widths based on which panels are open
  const getLeftWidth = () => {
    if (isMobile) return '100%';
    return leftSidebarOpen ? '280px' : '0px';
  };
  
  const getRightWidth = () => {
    if (isMobile || isTablet) return '100%';
    return rightPanelOpen ? '340px' : '0px';
  };
  
  const getCenterWidth = () => {
    if (isMobile) return '100%';
    
    if (isTablet) {
      return leftSidebarOpen ? 'calc(100% - 280px)' : '100%';
    }
    
    if (leftSidebarOpen && rightPanelOpen) return 'calc(100% - 620px)';
    if (leftSidebarOpen) return 'calc(100% - 280px)';
    if (rightPanelOpen) return 'calc(100% - 340px)';
    return '100%';
  };
  
  // Sidebar toggle handlers
  const toggleLeftSidebar = () => setLeftSidebarOpen(!leftSidebarOpen);
  const toggleRightPanel = () => setRightPanelOpen(!rightPanelOpen);
  
  // Animations
  const sidebarVariants = {
    open: { width: 'auto', opacity: 1, display: 'block' },
    closed: { width: 0, opacity: 0, transitionEnd: { display: 'none' } }
  };
  
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        height: '100vh',
        overflow: 'hidden',
        position: 'relative',
        ...sx
      }}
    >
      {/* Left Sidebar Toggle Button (Mobile) */}
      {isMobile && (
        <IconButton
          size="large"
          color="primary"
          aria-label="toggle sidebar"
          onClick={toggleLeftSidebar}
          sx={{
            position: 'fixed',
            top: 12,
            left: 12,
            zIndex: 1201,
            backgroundColor: 'rgba(18, 22, 32, 0.7)',
            backdropFilter: 'blur(4px)',
            '&:hover': {
              backgroundColor: 'rgba(18, 22, 32, 0.9)',
            }
          }}
        >
          {leftSidebarOpen ? <CloseIcon /> : <MenuIcon />}
        </IconButton>
      )}
      
      {/* Left Sidebar */}
      <AnimatePresence initial={false}>
        {(leftSidebarOpen || !isMobile) && (
          <Box
            component={motion.div}
            initial={isMobile ? "closed" : "open"}
            animate="open"
            exit="closed"
            variants={isMobile ? sidebarVariants : {}}
            transition={{ 
              type: 'spring', 
              stiffness: 400, 
              damping: 40 
            }}
            sx={{
              width: getLeftWidth(),
              height: '100%',
              borderRight: '1px solid rgba(255, 255, 255, 0.05)',
              backgroundColor: 'background.default',
              position: isMobile ? 'fixed' : 'relative',
              zIndex: isMobile ? 1200 : 'auto',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Box
              sx={{
                height: '100%',
                width: '280px',
                overflow: 'auto',
              }}
            >
              {leftSidebar}
            </Box>
          </Box>
        )}
      </AnimatePresence>
      
      {/* Center Panel */}
      <Box
        sx={{
          width: getCenterWidth(),
          height: '100%',
          overflow: 'auto',
          transition: 'width 0.3s ease',
          backgroundColor: 'background.default',
          display: isMobile && leftSidebarOpen ? 'none' : 'block',
        }}
      >
        {center}
      </Box>
      
      {/* Right Panel */}
      <AnimatePresence initial={false}>
        {rightPanelOpen && !(isMobile && leftSidebarOpen) && (
          <Box
            component={motion.div}
            initial={isTablet ? "closed" : "open"}
            animate="open"
            exit="closed"
            variants={isTablet ? sidebarVariants : {}}
            transition={{ 
              type: 'spring', 
              stiffness: 400, 
              damping: 40 
            }}
            sx={{
              width: getRightWidth(),
              height: '100%',
              borderLeft: '1px solid rgba(255, 255, 255, 0.05)',
              backgroundColor: 'background.paper',
              position: isTablet ? 'fixed' : 'relative',
              right: 0,
              zIndex: isTablet ? 1199 : 'auto',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Box
              sx={{
                height: '100%',
                width: '340px',
                overflow: 'auto',
              }}
            >
              {rightPanel}
            </Box>
          </Box>
        )}
      </AnimatePresence>
      
      {/* Right Panel Toggle Button */}
      {!isMobile && (
        <IconButton
          size="small"
          color="primary"
          aria-label="toggle results panel"
          onClick={toggleRightPanel}
          sx={{
            position: 'absolute',
            top: 16,
            right: rightPanelOpen ? 354 : 16,
            zIndex: 1100,
            backgroundColor: 'rgba(18, 22, 32, 0.7)',
            backdropFilter: 'blur(4px)',
            transition: 'right 0.3s ease',
            '&:hover': {
              backgroundColor: 'rgba(18, 22, 32, 0.9)',
            }
          }}
        >
          {rightPanelOpen ? <CloseIcon fontSize="small" /> : <MenuIcon fontSize="small" />}
        </IconButton>
      )}
    </Box>
  );
};

export default AppLayout; 