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
import { useTranslation } from 'react-i18next';

const Settings: React.FC = () => {
  const { t } = useTranslation();
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
        {t('settings.title')}
      </Typography>

      <Grid container spacing={3}>
        {/* Storage Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <StorageIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">{t('settings.storage.title') || 'Storage Management'}</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoCleanup}
                    onChange={(e) => handleSettingChange('autoCleanup', e.target.checked)}
                  />
                }
                label={t('settings.storage.autoCleanup') || 'Auto Cleanup Old Files'}
              />

              <Box sx={{ mt: 2 }}>
                <Typography gutterBottom>{t('settings.storage.maxSize') || 'Max Storage Size (GB)'}</Typography>
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
                label={t('settings.storage.retentionDays') || 'Retention Days'}
                type="number"
                value={settings.retentionDays}
                onChange={(e) => handleSettingChange('retentionDays', parseInt(e.target.value))}
                helperText={t('settings.storage.retentionHelperText') || 'Days to keep old files before cleanup'}
                sx={{ mt: 2 }}
              />

              <Button
                variant="outlined"
                startIcon={<DeleteIcon />}
                onClick={handleClearCache}
                sx={{ mt: 2 }}
                fullWidth
              >
                {t('settings.storage.clearCache') || 'Clear Cache'}
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
                <Typography variant="h6">{t('settings.performance.title')}</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableCaching}
                    onChange={(e) => handleSettingChange('enableCaching', e.target.checked)}
                  />
                }
                label={t('settings.performance.enableCaching') || 'Enable Caching'}
              />

              <Box sx={{ mt: 2 }}>
                <Typography gutterBottom>{t('settings.performance.maxWorkers')}</Typography>
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
                <Typography gutterBottom>{t('settings.performance.cacheSize')}</Typography>
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
                label={`${t('settings.indexing.interval')} (${t('common.minutes')})`}
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
                <Typography variant="h6">{t('settings.ai.title')}</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableAI}
                    onChange={(e) => handleSettingChange('enableAI', e.target.checked)}
                  />
                }
                label={t('settings.ai.enableSmartSearch') || 'Enable AI Features'}
              />

              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>{t('settings.ai.model')}</InputLabel>
                <Select
                  value={settings.aiModel}
                  label={t('settings.ai.model')}
                  onChange={(e) => handleSettingChange('aiModel', e.target.value)}
                  disabled={!settings.enableAI}
                >
                  <MenuItem value="llama3.2:3b">Llama 3.2 3B (Fast)</MenuItem>
                  <MenuItem value="llama3.2:7b">Llama 3.2 7B (Balanced)</MenuItem>
                  <MenuItem value="llama3.2:13b">Llama 3.2 13B (Accurate)</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>{t('settings.ai.embeddingModel') || 'Embedding Model'}</InputLabel>
                <Select
                  value={settings.embeddingModel}
                  label={t('settings.ai.embeddingModel') || 'Embedding Model'}
                  onChange={(e) => handleSettingChange('embeddingModel', e.target.value)}
                  disabled={!settings.enableAI}
                >
                  <MenuItem value="nomic-embed-text">Nomic Embed Text</MenuItem>
                  <MenuItem value="all-minilm">All MiniLM L6 v2</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label={t('settings.ai.maxTokens') || 'Max Tokens'}
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
                <Typography variant="h6">{t('settings.scheduling.title') || 'Automated Tasks'}</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoIndexing}
                    onChange={(e) => handleSettingChange('autoIndexing', e.target.checked)}
                  />
                }
                label={t('settings.indexing.enableAutoIndexing') || 'Enable Auto Indexing'}
              />

              <TextField
                fullWidth
                label={`${t('settings.indexing.fullIndexing')} (${t('settings.indexing.hours')})`}
                type="number"
                value={settings.fullIndexInterval}
                onChange={(e) => handleSettingChange('fullIndexInterval', parseInt(e.target.value))}
                disabled={!settings.autoIndexing}
                sx={{ mt: 2 }}
              />

              <TextField
                fullWidth
                label={`${t('settings.indexing.quickIndexing')} (${t('settings.indexing.minutes')})`}
                type="number"
                value={settings.quickIndexInterval}
                onChange={(e) => handleSettingChange('quickIndexInterval', parseInt(e.target.value))}
                disabled={!settings.autoIndexing}
                sx={{ mt: 2 }}
              />

              <TextField
                fullWidth
                label={`${t('settings.scheduling.cleanupInterval') || 'Cleanup Interval'} (${t('settings.indexing.hours')})`}
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
                <Typography variant="h6">{t('settings.general.notifications')}</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableNotifications}
                    onChange={(e) => handleSettingChange('enableNotifications', e.target.checked)}
                  />
                }
                label={t('settings.general.enableNotifications')}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifyOnCompletion}
                    onChange={(e) => handleSettingChange('notifyOnCompletion', e.target.checked)}
                    disabled={!settings.enableNotifications}
                  />
                }
                label={t('settings.notifications.notifyOnCompletion') || 'Notify on Task Completion'}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifyOnErrors}
                    onChange={(e) => handleSettingChange('notifyOnErrors', e.target.checked)}
                    disabled={!settings.enableNotifications}
                  />
                }
                label={t('settings.notifications.notifyOnErrors') || 'Notify on Errors'}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.emailNotifications}
                    onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                    disabled={!settings.enableNotifications}
                  />
                }
                label={t('settings.notifications.emailNotifications') || 'Email Notifications'}
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
                <Typography variant="h6">{t('settings.security.title') || 'Security'}</Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableEncryption}
                    onChange={(e) => handleSettingChange('enableEncryption', e.target.checked)}
                  />
                }
                label={t('settings.security.enableEncryption') || 'Enable Data Encryption'}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.requireAuth}
                    onChange={(e) => handleSettingChange('requireAuth', e.target.checked)}
                  />
                }
                label={t('settings.security.requireAuth') || 'Require Authentication'}
              />

              <TextField
                fullWidth
                label={`${t('settings.security.sessionTimeout') || 'Session Timeout'} (${t('common.minutes')})`}
                type="number"
                value={settings.sessionTimeout}
                onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                disabled={!settings.requireAuth}
                sx={{ mt: 2 }}
              />

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  {t('settings.security.inDevelopment') || 'Security features are currently in development.'}
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
                {t('settings.systemActions.title') || 'System Actions'}
              </Typography>
              <Grid container spacing={2}>
                <Grid item>
                  <Button
                    variant="contained"
                    onClick={handleSaveSettings}
                    startIcon={<SettingsIcon />}
                  >
                    {t('settings.actions.save')}
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    onClick={() => setBackupDialogOpen(true)}
                    startIcon={<BackupIcon />}
                  >
                    {t('settings.systemActions.backupDatabase') || 'Backup Database'}
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    onClick={() => setResetDialogOpen(true)}
                    startIcon={<RefreshIcon />}
                    color="warning"
                  >
                    {t('settings.actions.reset')}
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
                {t('settings.systemInfo.title') || 'System Information'}
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon><InfoIcon /></ListItemIcon>
                  <ListItemText
                    primary={t('settings.systemInfo.version') || 'Smart File Manager Version'}
                    secondary="v2.1.1"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><StorageIcon /></ListItemIcon>
                  <ListItemText
                    primary={t('settings.systemInfo.databaseSize') || 'Database Size'}
                    secondary="~50 MB (estimated)"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><PerformanceIcon /></ListItemIcon>
                  <ListItemText
                    primary={t('settings.systemInfo.cacheSize') || 'Cache Size'}
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
        <DialogTitle>{t('settings.dialogs.resetTitle') || 'Reset Settings'}</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            {t('settings.dialogs.resetWarning') || 'This will reset all settings to their default values. This action cannot be undone.'}
          </Alert>
          <Typography>
            {t('settings.dialogs.resetConfirm') || 'Are you sure you want to reset all settings to defaults?'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleResetSettings} color="warning" variant="contained">
            {t('common.reset') || 'Reset'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Backup Confirmation Dialog */}
      <Dialog
        open={backupDialogOpen}
        onClose={() => setBackupDialogOpen(false)}
      >
        <DialogTitle>{t('settings.dialogs.backupTitle') || 'Backup Database'}</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            {t('settings.dialogs.backupDescription') || 'This will create a backup of your file index database and settings.'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('settings.dialogs.backupLocation') || 'The backup will be saved to your Downloads folder.'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBackupDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleBackupDatabase} color="primary" variant="contained">
            {t('settings.actions.createBackup') || 'Create Backup'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings;