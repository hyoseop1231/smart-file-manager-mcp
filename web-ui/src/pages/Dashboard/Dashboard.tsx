import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  Skeleton,
  Button,
  Tooltip as MuiTooltip,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import axios from 'axios';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  // Fetch system health
  const { data: healthData, isLoading: healthLoading, refetch: refetchHealth } = useQuery(
    'health',
    () => axios.get('/health').then(res => res.data),
    { refetchInterval: 30000 }
  );

  // Fetch detailed metrics
  const { data: metricsData, isLoading: metricsLoading } = useQuery(
    'metrics',
    () => axios.get('/metrics').then(res => res.data),
    { refetchInterval: 60000 }
  );

  // Fetch recent files
  const { data: recentFiles } = useQuery(
    'recentFiles',
    () => axios.get('/recent?hours=24&limit=10').then(res => res.data),
    { refetchInterval: 300000 } // 5 minutes
  );

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleIcon color="success" />;
      case 'available': return <CheckCircleIcon color="success" />;
      case 'warning': return <WarningIcon color="warning" />;
      case 'error': return <ErrorIcon color="error" />;
      case 'unavailable': return <ErrorIcon color="error" />;
      default: return <CheckCircleIcon color="disabled" />;
    }
  };

  // Prepare chart data
  const categoryData = healthData?.db_stats?.by_category ? 
    Object.entries(healthData.db_stats.by_category).map(([category, count]) => ({
      name: category.charAt(0).toUpperCase() + category.slice(1),
      value: count,
    })) : [];

  const COLORS = ['#1976D2', '#00796B', '#FF6B35', '#9C27B0', '#F57C00', '#388E3C', '#D32F2F'];

  const performanceData = metricsData?.system_metrics ? [
    {
      name: 'CPU',
      current: metricsData.system_metrics.cpu_percent?.current || 0,
      average: metricsData.system_metrics.cpu_percent?.average || 0,
    },
    {
      name: 'Memory',
      current: metricsData.system_metrics.memory_percent?.current || 0,
      average: metricsData.system_metrics.memory_percent?.average || 0,
    },
    {
      name: 'Disk',
      current: metricsData.system_metrics.disk_usage?.current || 0,
      average: metricsData.system_metrics.disk_usage?.average || 0,
    },
  ] : [];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          {t('dashboard.title')}
        </Typography>
        <MuiTooltip title={t('dashboard.refresh')}>
          <IconButton onClick={() => refetchHealth()} color="primary">
            <RefreshIcon />
          </IconButton>
        </MuiTooltip>
      </Box>

      <Grid container spacing={3}>
        {/* System Status Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    {t('dashboard.systemHealth')}
                  </Typography>
                  {healthLoading ? (
                    <Skeleton width={80} height={32} />
                  ) : (
                    <Chip
                      label={t(`dashboard.${healthData?.status || 'healthy'}`)}
                      color={getStatusColor(healthData?.status)}
                      icon={getStatusIcon(healthData?.status)}
                    />
                  )}
                </Box>
                <CheckCircleIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card 
            sx={{ cursor: 'pointer', '&:hover': { boxShadow: 3 } }}
            onClick={() => navigate('/explorer')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    {t('dashboard.totalFiles')}
                  </Typography>
                  {healthLoading ? (
                    <Skeleton width={100} height={32} />
                  ) : (
                    <Typography variant="h4">
                      {healthData?.db_stats?.total_files?.toLocaleString() || 0}
                    </Typography>
                  )}
                </Box>
                <FileIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{ cursor: 'pointer', '&:hover': { boxShadow: 3 } }}
            onClick={() => navigate('/analytics')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    {t('dashboard.totalSize')}
                  </Typography>
                  {healthLoading ? (
                    <Skeleton width={80} height={32} />
                  ) : (
                    <Typography variant="h4">
                      {formatBytes((healthData?.db_stats?.total_size_gb || 0) * 1024 * 1024 * 1024)}
                    </Typography>
                  )}
                </Box>
                <StorageIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Background Tasks
                  </Typography>
                  {healthLoading ? (
                    <Skeleton width={40} height={32} />
                  ) : (
                    <Typography variant="h4">
                      {healthData?.background_tasks || 0}
                    </Typography>
                  )}
                </Box>
                <SpeedIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* File Category Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  {t('dashboard.fileActivity')}
                </Typography>
                <Button
                  size="small"
                  endIcon={<ArrowForwardIcon />}
                  onClick={() => navigate('/analytics')}
                >
                  {t('dashboard.viewDetails')}
                </Button>
              </Box>
              {categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Skeleton variant="rectangular" width="100%" height={300} />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* System Performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Performance
              </Typography>
              {performanceData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="current" fill="#1976D2" name="Current %" />
                    <Bar dataKey="average" fill="#00796B" name="Average %" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Skeleton variant="rectangular" width="100%" height={300} />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Service Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Service Status
              </Typography>
              {healthData?.services ? (
                <List dense>
                  {Object.entries(healthData.services).map(([service, status]) => (
                    <ListItem key={service}>
                      <ListItemIcon>
                        {getStatusIcon(status as string)}
                      </ListItemIcon>
                      <ListItemText
                        primary={service.charAt(0).toUpperCase() + service.slice(1)}
                        secondary={status as string}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Skeleton variant="rectangular" width="100%" height={200} />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Files (Last 24h)
              </Typography>
              {recentFiles?.files ? (
                <List dense>
                  {recentFiles.files.slice(0, 5).map((file: any, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <FolderIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={file.name}
                        secondary={`${formatBytes(file.size)} • ${new Date(file.modified * 1000).toLocaleDateString()}`}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Skeleton variant="rectangular" width="100%" height={200} />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Issues */}
        {metricsData?.issues && metricsData.issues.length > 0 && (
          <Grid item xs={12}>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Performance Issues Detected
              </Typography>
              {metricsData.issues.map((issue: string, index: number) => (
                <Typography key={index} variant="body2">
                  • {issue}
                </Typography>
              ))}
            </Alert>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default Dashboard;