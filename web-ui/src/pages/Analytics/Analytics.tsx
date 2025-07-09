import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  LinearProgress,
  Skeleton,
} from '@mui/material';
import {
  ContentCopy as DuplicateIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Storage as StorageIcon,
  Assessment as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  CloudUpload as CloudUploadIcon,
  Speed as SpeedIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Treemap,
} from 'recharts';
import axios from 'axios';

interface DuplicateGroup {
  duplicate_key: string;
  count: number;
  files: string[];
}

const Analytics: React.FC = () => {
  const [duplicateMethod, setDuplicateMethod] = useState('hash');
  const [minSize, setMinSize] = useState(1000);
  const [selectedDuplicates, setSelectedDuplicates] = useState<string[]>([]);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [previewFiles, setPreviewFiles] = useState<string[]>([]);

  // Fetch duplicates
  const { data: duplicatesData, isLoading: duplicatesLoading, refetch: refetchDuplicates } = useQuery(
    ['duplicates', duplicateMethod, minSize],
    () => axios.post('/duplicates', {
      method: duplicateMethod,
      minSize: minSize,
    }).then(res => res.data),
    {
      enabled: true,
    }
  );

  // Fetch system metrics
  const { data: metricsData, isLoading: metricsLoading } = useQuery(
    'detailedMetrics',
    () => axios.get('/metrics').then(res => res.data),
    {
      refetchInterval: 60000,
    }
  );

  // Fetch recent files for trend analysis
  const { data: recentFiles } = useQuery(
    'recentFilesAnalytics',
    () => axios.get('/recent?hours=168&limit=1000').then(res => res.data), // Last week
    {
      refetchInterval: 300000,
    }
  );

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const calculatePotentialSavings = (duplicates: DuplicateGroup[]) => {
    let totalSavings = 0;
    duplicates.forEach(group => {
      if (group.count > 1) {
        // Estimate savings by keeping one copy and removing others
        const estimatedFileSize = minSize; // Minimum size as estimate
        totalSavings += estimatedFileSize * (group.count - 1);
      }
    });
    return totalSavings;
  };

  const handlePreviewDuplicates = (files: string[]) => {
    setPreviewFiles(files);
    setPreviewDialogOpen(true);
  };

  const handleSelectDuplicateGroup = (groupKey: string) => {
    setSelectedDuplicates(prev =>
      prev.includes(groupKey)
        ? prev.filter(key => key !== groupKey)
        : [...prev, groupKey]
    );
  };

  // Prepare chart data
  const performanceData = metricsData?.system_metrics ? [
    {
      metric: 'CPU Usage',
      current: metricsData.system_metrics.cpu_percent?.current || 0,
      average: metricsData.system_metrics.cpu_percent?.average || 0,
      max: metricsData.system_metrics.cpu_percent?.max || 0,
    },
    {
      metric: 'Memory Usage',
      current: metricsData.system_metrics.memory_percent?.current || 0,
      average: metricsData.system_metrics.memory_percent?.average || 0,
      max: metricsData.system_metrics.memory_percent?.max || 0,
    },
    {
      metric: 'Disk Usage',
      current: metricsData.system_metrics.disk_usage?.current || 0,
      average: metricsData.system_metrics.disk_usage?.average || 0,
      max: metricsData.system_metrics.disk_usage?.max || 0,
    },
  ] : [];

  // Process file activity data
  const activityData = recentFiles?.files ? 
    recentFiles.files.reduce((acc: any[], file: any) => {
      const date = new Date(file.modified * 1000).toLocaleDateString();
      const existing = acc.find(item => item.date === date);
      if (existing) {
        existing.files += 1;
        existing.size += file.size;
      } else {
        acc.push({ date, files: 1, size: file.size });
      }
      return acc;
    }, []).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()) : [];

  const duplicateGroups = duplicatesData?.duplicates || [];
  const potentialSavings = calculatePotentialSavings(duplicateGroups);

  const COLORS = ['#1976D2', '#00796B', '#FF6B35', '#9C27B0', '#F57C00', '#388E3C', '#D32F2F'];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          File Analytics & Insights
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => {
            refetchDuplicates();
          }}
        >
          Refresh Data
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Storage Analytics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Duplicates Found
                  </Typography>
                  <Typography variant="h4">
                    {duplicatesData?.duplicates_found || 0}
                  </Typography>
                </Box>
                <DuplicateIcon sx={{ fontSize: 40, color: 'warning.main' }} />
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
                    Potential Savings
                  </Typography>
                  <Typography variant="h4">
                    {formatBytes(potentialSavings)}
                  </Typography>
                </Box>
                <StorageIcon sx={{ fontSize: 40, color: 'success.main' }} />
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
                    Avg CPU Usage
                  </Typography>
                  <Typography variant="h4">
                    {metricsData?.system_metrics?.cpu_percent?.average?.toFixed(1) || 0}%
                  </Typography>
                </Box>
                <SpeedIcon sx={{ fontSize: 40, color: 'info.main' }} />
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
                    Active Files
                  </Typography>
                  <Typography variant="h4">
                    {recentFiles?.count || 0}
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Duplicate Detection */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Duplicate File Detection
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <InputLabel>Method</InputLabel>
                    <Select
                      value={duplicateMethod}
                      label="Method"
                      onChange={(e) => setDuplicateMethod(e.target.value)}
                    >
                      <MenuItem value="hash">Content Hash</MenuItem>
                      <MenuItem value="name">File Name</MenuItem>
                      <MenuItem value="size">File Size</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <InputLabel>Min Size</InputLabel>
                    <Select
                      value={minSize}
                      label="Min Size"
                      onChange={(e) => setMinSize(Number(e.target.value))}
                    >
                      <MenuItem value={0}>All Files</MenuItem>
                      <MenuItem value={1024}>1 KB+</MenuItem>
                      <MenuItem value={1048576}>1 MB+</MenuItem>
                      <MenuItem value={10485760}>10 MB+</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              </Box>

              {duplicatesLoading ? (
                <Box>
                  {Array.from({ length: 5 }).map((_, index) => (
                    <Skeleton key={index} height={60} sx={{ mb: 1 }} />
                  ))}
                </Box>
              ) : duplicateGroups.length > 0 ? (
                <Box>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Found {duplicateGroups.length} duplicate groups. 
                    Potential savings: {formatBytes(potentialSavings)}
                  </Alert>
                  <List>
                    {duplicateGroups.slice(0, 10).map((group: DuplicateGroup, index) => (
                      <ListItem
                        key={group.duplicate_key}
                        sx={{
                          border: 1,
                          borderColor: 'divider',
                          borderRadius: 1,
                          mb: 1,
                        }}
                      >
                        <ListItemIcon>
                          <DuplicateIcon color="warning" />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body1">
                                {duplicateMethod === 'hash' ? 'Identical Content' :
                                 duplicateMethod === 'name' ? group.duplicate_key :
                                 formatBytes(Number(group.duplicate_key))}
                              </Typography>
                              <Chip
                                label={`${group.count} files`}
                                size="small"
                                color="warning"
                              />
                            </Box>
                          }
                          secondary={
                            duplicateMethod === 'name' ? 
                              `File name: ${group.duplicate_key}` :
                              duplicateMethod === 'size' ?
                                `File size: ${formatBytes(Number(group.duplicate_key))}` :
                                `Hash: ${group.duplicate_key.substring(0, 16)}...`
                          }
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            onClick={() => handlePreviewDuplicates(group.files)}
                            color="primary"
                          >
                            <ViewIcon />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              ) : (
                <Alert severity="success">
                  No duplicates found with current criteria.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* System Performance */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Performance
              </Typography>
              {performanceData.length > 0 ? (
                <Box>
                  {performanceData.map((metric, index) => (
                    <Box key={metric.metric} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">{metric.metric}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {metric.current.toFixed(1)}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={metric.current}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: metric.current > 80 ? 'error.main' :
                                           metric.current > 60 ? 'warning.main' : 'success.main',
                          },
                        }}
                      />
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          Avg: {metric.average.toFixed(1)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Peak: {metric.max.toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Skeleton variant="rectangular" height={200} />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* File Activity Trends */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                File Activity Trends (Last 7 Days)
              </Typography>
              {activityData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={activityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="files"
                      stackId="1"
                      stroke="#1976D2"
                      fill="#1976D2"
                      fillOpacity={0.3}
                      name="Files Modified"
                    />
                    <Area
                      yAxisId="right"
                      type="monotone"
                      dataKey="size"
                      stackId="2"
                      stroke="#00796B"
                      fill="#00796B"
                      fillOpacity={0.3}
                      name="Data Volume (bytes)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <Skeleton variant="rectangular" height={300} />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Insights */}
        {metricsData?.issues && metricsData.issues.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom color="warning.main">
                  Performance Insights & Recommendations
                </Typography>
                <List>
                  {metricsData.issues.map((issue: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <AnalyticsIcon color="warning" />
                      </ListItemIcon>
                      <ListItemText primary={issue} />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Duplicate Preview Dialog */}
      <Dialog
        open={previewDialogOpen}
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Duplicate Files Preview
        </DialogTitle>
        <DialogContent>
          <List>
            {previewFiles.map((filePath, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <DuplicateIcon />
                </ListItemIcon>
                <ListItemText
                  primary={filePath.split('/').pop()}
                  secondary={filePath}
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>
            Close
          </Button>
          <Button variant="contained" color="error" startIcon={<DeleteIcon />}>
            Delete Duplicates
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Analytics;