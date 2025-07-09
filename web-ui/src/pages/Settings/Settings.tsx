import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
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
  Slider,
  Paper,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Speed as PerformanceIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Schedule as ScheduleIcon,
  Assessment as AnalyticsIcon,
  Backup as BackupIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

const Settings: React.FC = () => {
  const [settings, setSettings] = useState({
    // Storage Settings
    autoCleanup: true,
    maxStorageSize: 100, // GB
    retentionDays: 30,
    
    // Performance Settings
    maxConcurrentJobs: 4,
    indexingInterval: 30, // minutes
    enableCaching: true,
    cacheSize: 1024, // MB
    
    // AI/LLM Settings
    enableAI: true,
    aiModel: 'llama3.2:3b',
    embeddingModel: 'nomic-embed-text',
    maxTokens: 2048,
    
    // Notifications
    enableNotifications: true,
    notifyOnCompletion: true,
    notifyOnErrors: true,
    emailNotifications: false,
    
    // Security
    enableEncryption: false,
    requireAuth: false,
    sessionTimeout: 60, // minutes
    
    // Scheduling
    autoIndexing: true,
    fullIndexInterval: 2, // hours
    quickIndexInterval: 30, // minutes
    cleanupInterval: 24, // hours
  });

  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [backupDialogOpen, setBackupDialogOpen] = useState(false);

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveSettings = () => {
    // Save settings logic here
    console.log('Saving settings:', settings);
  };

  const handleResetSettings = () => {
    // Reset to defaults
    setResetDialogOpen(false);
    // Reset logic here
  };

  const handleBackupDatabase = () => {
    // Backup logic here
    setBackupDialogOpen(false);
  };

  const handleClearCache = () => {
    // Clear cache logic
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        System Settings
      </Typography>

      <Grid container spacing={3}>
        {/* Storage Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <StorageIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Storage Management</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoCleanup}
                    onChange={(e) => handleSettingChange('autoCleanup', e.target.checked)}
                  />
                }
                label="Auto Cleanup Old Files"
              />

              <Box sx={{ mt: 2 }}>
                <Typography gutterBottom>Max Storage Size (GB)</Typography>
                <Slider
                  value={settings.maxStorageSize}
                  onChange={(e, value) => handleSettingChange('maxStorageSize', value)}
                  min={10}
                  max={1000}
                  valueLabelDisplay="auto"
                />
              </Box>

              <TextField
                fullWidth
                label="Retention Days"
                type="number"
                value={settings.retentionDays}
                onChange={(e) => handleSettingChange('retentionDays', parseInt(e.target.value))}
                helperText="Days to keep old files before cleanup"
                sx={{ mt: 2 }}
              />

              <Button
                variant="outlined"
                startIcon={<DeleteIcon />}
                onClick={handleClearCache}
                sx={{ mt: 2 }}
                fullWidth
              >
                Clear Cache
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PerformanceIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Performance</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableCaching}
                    onChange={(e) => handleSettingChange('enableCaching', e.target.checked)}
                  />
                }
                label="Enable Caching"
              />

              <Box sx={{ mt: 2 }}>
                <Typography gutterBottom>Max Concurrent Jobs</Typography>
                <Slider
                  value={settings.maxConcurrentJobs}
                  onChange={(e, value) => handleSettingChange('maxConcurrentJobs', value)}
                  min={1}
                  max={16}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>

              <Box sx={{ mt: 2 }}>
                <Typography gutterBottom>Cache Size (MB)</Typography>
                <Slider
                  value={settings.cacheSize}
                  onChange={(e, value) => handleSettingChange('cacheSize', value)}
                  min={256}
                  max={8192}
                  step={256}
                  valueLabelDisplay="auto"
                />
              </Box>

              <TextField
                fullWidth
                label="Indexing Interval (minutes)"
                type="number"
                value={settings.indexingInterval}
                onChange={(e) => handleSettingChange('indexingInterval', parseInt(e.target.value))}
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* AI/LLM Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AnalyticsIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">AI Configuration</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableAI}
                    onChange={(e) => handleSettingChange('enableAI', e.target.checked)}
                  />
                }
                label="Enable AI Features"
              />

              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>AI Model</InputLabel>
                <Select
                  value={settings.aiModel}
                  label="AI Model"
                  onChange={(e) => handleSettingChange('aiModel', e.target.value)}
                  disabled={!settings.enableAI}
                >
                  <MenuItem value="llama3.2:3b">Llama 3.2 3B (Fast)</MenuItem>
                  <MenuItem value="llama3.2:7b">Llama 3.2 7B (Balanced)</MenuItem>
                  <MenuItem value="llama3.2:13b">Llama 3.2 13B (Accurate)</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>Embedding Model</InputLabel>
                <Select
                  value={settings.embeddingModel}
                  label="Embedding Model"
                  onChange={(e) => handleSettingChange('embeddingModel', e.target.value)}
                  disabled={!settings.enableAI}
                >
                  <MenuItem value="nomic-embed-text">Nomic Embed Text</MenuItem>
                  <MenuItem value="all-minilm">All MiniLM L6 v2</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Max Tokens"
                type="number"
                value={settings.maxTokens}
                onChange={(e) => handleSettingChange('maxTokens', parseInt(e.target.value))}
                disabled={!settings.enableAI}
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Scheduling Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ScheduleIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Automated Tasks</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoIndexing}
                    onChange={(e) => handleSettingChange('autoIndexing', e.target.checked)}
                  />
                }
                label="Enable Auto Indexing"
              />

              <TextField
                fullWidth
                label="Full Index Interval (hours)"
                type="number"
                value={settings.fullIndexInterval}
                onChange={(e) => handleSettingChange('fullIndexInterval', parseInt(e.target.value))}
                disabled={!settings.autoIndexing}
                sx={{ mt: 2 }}
              />

              <TextField
                fullWidth
                label="Quick Index Interval (minutes)"
                type="number"
                value={settings.quickIndexInterval}
                onChange={(e) => handleSettingChange('quickIndexInterval', parseInt(e.target.value))}
                disabled={!settings.autoIndexing}
                sx={{ mt: 2 }}
              />

              <TextField
                fullWidth
                label="Cleanup Interval (hours)"
                type="number"
                value={settings.cleanupInterval}
                onChange={(e) => handleSettingChange('cleanupInterval', parseInt(e.target.value))}
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Notifications */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <NotificationsIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Notifications</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableNotifications}
                    onChange={(e) => handleSettingChange('enableNotifications', e.target.checked)}
                  />
                }
                label="Enable Notifications"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifyOnCompletion}
                    onChange={(e) => handleSettingChange('notifyOnCompletion', e.target.checked)}
                    disabled={!settings.enableNotifications}
                  />
                }
                label="Notify on Task Completion"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifyOnErrors}
                    onChange={(e) => handleSettingChange('notifyOnErrors', e.target.checked)}
                    disabled={!settings.enableNotifications}
                  />
                }
                label="Notify on Errors"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.emailNotifications}
                    onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                    disabled={!settings.enableNotifications}
                  />
                }
                label="Email Notifications"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Security */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SecurityIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Security</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableEncryption}
                    onChange={(e) => handleSettingChange('enableEncryption', e.target.checked)}
                  />
                }
                label="Enable Data Encryption"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.requireAuth}
                    onChange={(e) => handleSettingChange('requireAuth', e.target.checked)}
                  />
                }
                label="Require Authentication"
              />

              <TextField
                fullWidth
                label="Session Timeout (minutes)"
                type="number"
                value={settings.sessionTimeout}
                onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                disabled={!settings.requireAuth}
                sx={{ mt: 2 }}
              />

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Security features are currently in development.
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>

        {/* System Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item>
                  <Button
                    variant="contained"
                    onClick={handleSaveSettings}
                    startIcon={<SettingsIcon />}
                  >
                    Save Settings
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    onClick={() => setBackupDialogOpen(true)}
                    startIcon={<BackupIcon />}
                  >
                    Backup Database
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    onClick={() => setResetDialogOpen(true)}
                    startIcon={<RefreshIcon />}
                    color="warning"
                  >
                    Reset to Defaults
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* System Information */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Information
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon><InfoIcon /></ListItemIcon>
                  <ListItemText
                    primary="Smart File Manager Version"
                    secondary="v2.1.1"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><StorageIcon /></ListItemIcon>
                  <ListItemText
                    primary="Database Size"
                    secondary="~50 MB (estimated)"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><PerformanceIcon /></ListItemIcon>
                  <ListItemText
                    primary="Cache Size"
                    secondary={formatBytes(settings.cacheSize * 1024 * 1024)}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Reset Confirmation Dialog */}
      <Dialog
        open={resetDialogOpen}
        onClose={() => setResetDialogOpen(false)}
      >
        <DialogTitle>Reset Settings</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will reset all settings to their default values. This action cannot be undone.
          </Alert>
          <Typography>
            Are you sure you want to reset all settings to defaults?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleResetSettings} color="warning" variant="contained">
            Reset
          </Button>
        </DialogActions>
      </Dialog>

      {/* Backup Confirmation Dialog */}
      <Dialog
        open={backupDialogOpen}
        onClose={() => setBackupDialogOpen(false)}
      >
        <DialogTitle>Backup Database</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            This will create a backup of your file index database and settings.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            The backup will be saved to your Downloads folder.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBackupDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleBackupDatabase} color="primary" variant="contained">
            Create Backup
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings;