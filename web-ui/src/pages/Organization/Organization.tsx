import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Stepper,
  Step,
  StepLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Skeleton,
  Paper,
  IconButton,
} from '@mui/material';
import {
  AutoAwesome as AIIcon,
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  Preview as PreviewIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Schedule as ScheduleIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from 'react-query';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

interface OrganizationTask {
  task_id: string;
  status: 'running' | 'completed' | 'failed';
  progress?: number;
  started_at: string;
  completed_at?: string;
  results?: any;
  error?: string;
}

const Organization: React.FC = () => {
  const { t } = useTranslation();
  const [activeStep, setActiveStep] = useState(0);
  const [sourceDir, setSourceDir] = useState('/Users/hyoseop1231/Desktop');
  const [targetDir, setTargetDir] = useState('');
  const [organizationMethod, setOrganizationMethod] = useState('content');
  const [useLLM, setUseLLM] = useState(true);
  const [dryRun, setDryRun] = useState(true);
  const [previewData, setPreviewData] = useState<any>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);

  const steps = [
    t('organization.steps.selectSource'),
    t('organization.steps.preview'),
    t('organization.steps.apply'),
    t('common.results') || 'Results'
  ];

  // Fetch active organization tasks
  const { data: activeTasks, refetch: refetchTasks } = useQuery(
    'organizationTasks',
    async () => {
      // This would fetch a list of active tasks from a tasks endpoint
      // For now, we'll simulate with the current task
      if (currentTaskId) {
        const response = await axios.get(`/task/${currentTaskId}`);
        return [response.data];
      }
      return [];
    },
    {
      enabled: !!currentTaskId,
      refetchInterval: 2000,
    }
  );

  // Organization mutation
  const organizationMutation = useMutation(
    async (params: any) => {
      const response = await axios.post('/organize', {
        sourceDir: params.sourceDir,
        targetDir: params.targetDir || `${params.sourceDir}/Organized`,
        method: params.method,
        dryRun: params.dryRun,
        use_llm: params.useLLM,
      });
      return response.data;
    },
    {
      onSuccess: (data) => {
        if (data.task_id) {
          setCurrentTaskId(data.task_id);
          setActiveStep(3);
        } else {
          setPreviewData(data);
          setActiveStep(1);
        }
      },
    }
  );

  const handlePreview = () => {
    organizationMutation.mutate({
      sourceDir,
      targetDir,
      method: organizationMethod,
      dryRun: true,
      useLLM,
    });
  };

  const handleExecute = () => {
    setConfirmDialogOpen(false);
    organizationMutation.mutate({
      sourceDir,
      targetDir,
      method: organizationMethod,
      dryRun: false,
      useLLM,
    });
  };

  const handleReset = () => {
    setActiveStep(0);
    setPreviewData(null);
    setCurrentTaskId(null);
    setDryRun(true);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getMethodDescription = (method: string) => {
    const descriptions = {
      content: t('organization.options.byContent'),
      date: t('organization.options.byDate'),
      extension: t('organization.options.byType'),
    };
    return descriptions[method as keyof typeof descriptions] || '';
  };

  const renderConfigurationStep = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('organization.sourceSelection.title')}
            </Typography>
            <TextField
              fullWidth
              label={t('organization.sourceSelection.selectDirectory')}
              value={sourceDir}
              onChange={(e) => setSourceDir(e.target.value)}
              helperText={t('organization.sourceHelperText') || 'Directory containing files to organize'}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label={t('organization.options.targetDirectory') + ' ' + t('common.optional', '(Optional)')}
              value={targetDir}
              onChange={(e) => setTargetDir(e.target.value)}
              helperText={t('organization.targetHelperText') || "Leave empty to create 'Organized' folder in source"}
              sx={{ mb: 2 }}
            />
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('organization.options.method')}
            </Typography>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>{t('organization.options.method')}</InputLabel>
              <Select
                value={organizationMethod}
                label={t('organization.options.method')}
                onChange={(e) => setOrganizationMethod(e.target.value)}
              >
                <MenuItem value="content">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AIIcon color="primary" />
                    {t('organization.options.byContent')}
                  </Box>
                </MenuItem>
                <MenuItem value="date">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ScheduleIcon color="primary" />
                    {t('organization.options.byDate')}
                  </Box>
                </MenuItem>
                <MenuItem value="extension">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SettingsIcon color="primary" />
                    {t('organization.options.byType')}
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              {getMethodDescription(organizationMethod)}
            </Alert>

            <FormControlLabel
              control={
                <Switch
                  checked={useLLM}
                  onChange={(e) => setUseLLM(e.target.checked)}
                  disabled={organizationMethod !== 'content'}
                />
              }
              label={t('organization.options.useAIEnhancement') || 'Use AI Enhancement'}
            />
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button variant="outlined" onClick={handleReset}>
            {t('common.reset') || 'Reset'}
          </Button>
          <Button
            variant="contained"
            onClick={handlePreview}
            disabled={!sourceDir || organizationMutation.isLoading}
            startIcon={<PreviewIcon />}
          >
            {t('organization.actions.preview') || 'Preview Organization'}
          </Button>
        </Box>
      </Grid>
    </Grid>
  );

  const renderPreviewStep = () => {
    if (organizationMutation.isLoading) {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <LinearProgress sx={{ mb: 2 }} />
          <Typography>{t('organization.progress.analyzing')}</Typography>
        </Box>
      );
    }

    if (!previewData?.results?.operations) {
      return (
        <Alert severity="error">
          {t('organization.errors.noPreviewData') || 'No preview data available. Please try again.'}
        </Alert>
      );
    }

    const operations = previewData.results.operations;
    const groupedOperations = operations.reduce((acc: any, op: any) => {
      const targetFolder = op.target.split('/').slice(-2, -1)[0] || 'Root';
      if (!acc[targetFolder]) {
        acc[targetFolder] = [];
      }
      acc[targetFolder].push(op);
      return acc;
    }, {});

    return (
      <Box>
        <Alert severity="info" sx={{ mb: 3 }}>
          {t('organization.preview.previewDescription', { 
            fileCount: operations.length, 
            categoryCount: Object.keys(groupedOperations).length 
          }) || `Preview shows ${operations.length} files will be organized into ${Object.keys(groupedOperations).length} categories. This is a preview only - no files will be moved yet.`}
        </Alert>

        <Grid container spacing={2}>
          {Object.entries(groupedOperations).map(([folder, ops]: [string, any]) => (
            <Grid item xs={12} md={6} key={folder}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <FolderIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">{folder}</Typography>
                  <Chip
                    label={`${ops.length} ${t('common.files') || 'files'}`}
                    size="small"
                    sx={{ ml: 'auto' }}
                  />
                </Box>
                <List dense>
                  {ops.slice(0, 5).map((op: any, index: number) => (
                    <ListItem key={index} sx={{ py: 0 }}>
                      <ListItemIcon sx={{ minWidth: 30 }}>
                        <FileIcon fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={op.source.split('/').pop()}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                  {ops.length > 5 && (
                    <ListItem>
                      <ListItemText
                        primary={t('common.andMore', { count: ops.length - 5 }) || `... and ${ops.length - 5} more files`}
                        primaryTypographyProps={{ 
                          variant: 'body2', 
                          color: 'text.secondary',
                          fontStyle: 'italic'
                        }}
                      />
                    </ListItem>
                  )}
                </List>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button variant="outlined" onClick={() => setActiveStep(0)}>
            {t('organization.actions.back')}
          </Button>
          <Button
            variant="contained"
            onClick={() => setConfirmDialogOpen(true)}
            startIcon={<StartIcon />}
            color="warning"
          >
            {t('organization.actions.apply')}
          </Button>
        </Box>
      </Box>
    );
  };

  const renderResultsStep = () => {
    const currentTask = activeTasks?.[0];

    if (!currentTask) {
      return (
        <Alert severity="error">
          {t('organization.errors.noActiveTask') || 'No active organization task found.'}
        </Alert>
      );
    }

    return (
      <Box>
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="h6">
                {t('organization.status.title') || 'Organization Status'}
              </Typography>
              <Chip
                label={currentTask.status}
                color={
                  currentTask.status === 'completed' ? 'success' :
                  currentTask.status === 'failed' ? 'error' : 'warning'
                }
                icon={
                  currentTask.status === 'completed' ? <CheckIcon /> :
                  currentTask.status === 'failed' ? <StopIcon /> : undefined
                }
              />
            </Box>

            {currentTask.status === 'running' && (
              <Box sx={{ mb: 2 }}>
                <LinearProgress 
                  variant={currentTask.progress ? 'determinate' : 'indeterminate'}
                  value={currentTask.progress}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {currentTask.progress ? `${currentTask.progress}% ${t('common.complete') || 'complete'}` : t('common.processing') || 'Processing...'}
                </Typography>
              </Box>
            )}

            <Typography variant="body2" color="text.secondary">
              {t('common.started') || 'Started'}: {new Date(currentTask.started_at).toLocaleString()}
              {currentTask.completed_at && (
                <><br />{t('common.completed') || 'Completed'}: {new Date(currentTask.completed_at).toLocaleString()}</>
              )}
            </Typography>
          </CardContent>
        </Card>

        {currentTask.status === 'completed' && currentTask.results && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('organization.results.summary') || 'Results Summary'}
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {currentTask.results.files_moved || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('organization.progress.filesOrganized', { count: currentTask.results.files_moved || 0 })}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {currentTask.results.folders_created || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('organization.results.foldersCreated') || 'Folders Created'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="info.main">
                      {formatBytes(currentTask.results.total_size || 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('organization.results.dataOrganized') || 'Data Organized'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="warning.main">
                      {currentTask.results.errors || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('common.errors') || 'Errors'}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}

        {currentTask.status === 'failed' && (
          <Alert severity="error">
            {t('organization.progress.error')}: {currentTask.error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button variant="outlined" onClick={() => refetchTasks()}>
            <RefreshIcon sx={{ mr: 1 }} />
            {t('common.refresh')}
          </Button>
          {currentTask.status !== 'running' && (
            <Button variant="contained" onClick={handleReset}>
              {t('organization.actions.startOrganizing')}
            </Button>
          )}
        </Box>
      </Box>
    );
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return renderConfigurationStep();
      case 1:
        return renderPreviewStep();
      case 2:
        return renderResultsStep();
      case 3:
        return renderResultsStep();
      default:
        return null;
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {t('organization.title')}
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {renderStepContent()}
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
      >
        <DialogTitle>
          {t('dialogs.organizationWarning.title')}
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            {t('dialogs.organizationWarning.message')} {previewData?.results?.operations?.length || 0} {t('common.files') || 'files'}.
            {t('dialogs.organizationWarning.cannotUndo') || 'This action cannot be easily undone.'}
          </Alert>
          <Typography>
            {t('dialogs.organizationWarning.confirmProceed') || 'Are you sure you want to proceed with organizing files from:'}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1, fontFamily: 'monospace' }}>
            {sourceDir}
          </Typography>
          <Typography sx={{ mt: 1 }}>
            {t('common.to')}:
          </Typography>
          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
            {targetDir || `${sourceDir}/Organized`}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>
            {t('common.cancel')}
          </Button>
          <Button
            variant="contained"
            color="warning"
            onClick={handleExecute}
            disabled={organizationMutation.isLoading}
          >
            {t('common.yes')}, {t('organization.actions.startOrganizing')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Organization;