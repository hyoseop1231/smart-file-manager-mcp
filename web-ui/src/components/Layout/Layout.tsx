import React, { useState } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  useTheme,
  useMediaQuery,
  Badge,
  Avatar,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Folder as FolderIcon,
  Analytics as AnalyticsIcon,
  AutoAwesome as OrganizeIcon,
  Settings as SettingsIcon,
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  Brightness4 as DarkModeIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import LanguageSwitcher from '../LanguageSwitcher/LanguageSwitcher';

interface LayoutProps {
  children: React.ReactNode;
}

const drawerWidth = 280;

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);

  const navigationItems = [
    { path: '/', label: t('nav.dashboard'), icon: DashboardIcon },
    { path: '/explorer', label: t('nav.fileExplorer'), icon: FolderIcon },
    { path: '/analytics', label: t('nav.analytics'), icon: AnalyticsIcon },
    { path: '/organization', label: t('nav.organization'), icon: OrganizeIcon },
    { path: '/settings', label: t('nav.settings'), icon: SettingsIcon },
  ];

  // Fetch system status for header
  const { data: systemStatus } = useQuery(
    'systemStatus',
    () => axios.get('/health').then(res => res.data),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const drawer = (
    <Box sx={{ overflow: 'auto' }}>
      {/* Logo and Title */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <StorageIcon color="primary" sx={{ fontSize: 32 }} />
          <Box>
            <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
              {t('app.title')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('app.subtitle')}
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Storage Usage */}
      {systemStatus?.db_stats && (
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Storage Overview
          </Typography>
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2">
              {systemStatus.db_stats.total_files?.toLocaleString() || 0} files
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {formatBytes((systemStatus.db_stats.total_size_gb || 0) * 1024 * 1024 * 1024)}
            </Typography>
          </Box>
          <Box sx={{ 
            height: 6, 
            bgcolor: 'grey.200', 
            borderRadius: 3,
            overflow: 'hidden',
          }}>
            <Box
              sx={{
                height: '100%',
                bgcolor: 'primary.main',
                width: `${Math.min((systemStatus.db_stats.total_size_gb || 0) / 100 * 100, 100)}%`,
                transition: 'width 0.3s ease',
              }}
            />
          </Box>
        </Box>
      )}

      {/* Navigation */}
      <List sx={{ px: 1 }}>
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <ListItem
              key={item.path}
              button
              onClick={() => {
                navigate(item.path);
                if (isMobile) setMobileOpen(false);
              }}
              sx={{
                borderRadius: 1,
                mb: 0.5,
                backgroundColor: isActive ? 'primary.main' : 'transparent',
                color: isActive ? 'primary.contrastText' : 'text.primary',
                '&:hover': {
                  backgroundColor: isActive ? 'primary.dark' : 'action.hover',
                },
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                <Icon />
              </ListItemIcon>
              <ListItemText 
                primary={item.label}
                primaryTypographyProps={{
                  fontWeight: isActive ? 600 : 400,
                }}
              />
            </ListItem>
          );
        })}
      </List>

      {/* Quick Stats */}
      {systemStatus?.db_stats?.by_category && (
        <Box sx={{ p: 2, mt: 'auto' }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            File Categories
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {Object.entries(systemStatus.db_stats.by_category).slice(0, 5).map(([category, count]) => (
              <Box key={category} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                  {category}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {(count as number).toLocaleString()}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          backgroundColor: 'background.paper',
          color: 'text.primary',
          boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.1)',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {navigationItems.find(item => item.path === location.pathname)?.label || 'Smart File Manager'}
          </Typography>

          {/* Header Actions */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton color="inherit">
              <SearchIcon />
            </IconButton>
            
            <IconButton color="inherit">
              <Badge badgeContent={systemStatus?.background_tasks || 0} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>

            <LanguageSwitcher />

            <IconButton color="inherit">
              <DarkModeIcon />
            </IconButton>

            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
              U
            </Avatar>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={isMobile ? mobileOpen : true}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: '1px solid',
              borderColor: 'divider',
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Toolbar />
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;