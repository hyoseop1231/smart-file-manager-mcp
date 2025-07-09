import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  IconButton,
  Button,
  Chip,
  Typography,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Checkbox,
  Menu,
  MenuItem,
  Tabs,
  Tab,
  Pagination,
  Skeleton,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  Switch,
  FormControlLabel,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  ViewList as ListViewIcon,
  ViewModule as GridViewIcon,
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  GetApp as DownloadIcon,
  Share as ShareIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  Add as AddIcon,
  Upload as UploadIcon,
  CreateNewFolder as NewFolderIcon,
  Clear as ClearIcon,
  SelectAll as SelectAllIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useTranslation } from 'react-i18next';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';
import { ko, enUS } from 'date-fns/locale';

interface FileItem {
  path: string;
  name: string;
  size: number;
  modified: number;
  metadata: {
    extension: string;
    category: string;
    is_hidden: boolean;
  };
}

const FileExplorer: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState('modified');
  const [filterOpen, setFilterOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [actionMenuAnchor, setActionMenuAnchor] = useState<null | HTMLElement>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  
  // Filters
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [sizeFilter, setSizeFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [showHidden, setShowHidden] = useState(false);

  const itemsPerPage = 50;

  // Search files
  const { data: searchResults, isLoading: searchLoading, refetch } = useQuery(
    ['fileSearch', searchQuery, currentPage, sortBy, categoryFilter, sizeFilter, dateFilter],
    async () => {
      let query = searchQuery;
      
      // Add filters to query
      if (categoryFilter !== 'all') {
        query += ` category:${categoryFilter}`;
      }
      if (sizeFilter !== 'all') {
        const sizeMap: { [key: string]: string } = {
          'small': 'size:<1MB',
          'medium': 'size:1MB-10MB',
          'large': 'size:>10MB',
        };
        query += ` ${sizeMap[sizeFilter]}`;
      }
      if (dateFilter !== 'all') {
        const dateMap: { [key: string]: string } = {
          'today': 'modified:today',
          'week': 'modified:week',
          'month': 'modified:month',
        };
        query += ` ${dateMap[dateFilter]}`;
      }

      const response = await axios.post('/search', {
        query: query || '*',
        use_llm: false,
        limit: itemsPerPage,
        offset: (currentPage - 1) * itemsPerPage,
      });
      return response.data;
    },
    {
      enabled: true,
      keepPreviousData: true,
    }
  );

  // File upload handling
  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Handle file upload logic here
    console.log('Files dropped:', acceptedFiles);
    setUploadDialogOpen(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
  });

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (category: string) => {
    const iconMap: { [key: string]: React.ReactElement } = {
      'image': <FileIcon sx={{ color: '#FF6B35' }} />,
      'video': <FileIcon sx={{ color: '#9C27B0' }} />,
      'audio': <FileIcon sx={{ color: '#00796B' }} />,
      'document': <FileIcon sx={{ color: '#1976D2' }} />,
      'code': <FileIcon sx={{ color: '#388E3C' }} />,
      'archive': <FileIcon sx={{ color: '#F57C00' }} />,
      'other': <FileIcon sx={{ color: '#757575' }} />,
    };
    return iconMap[category] || iconMap['other'];
  };

  const handleSelectFile = (filePath: string) => {
    setSelectedFiles(prev =>
      prev.includes(filePath)
        ? prev.filter(path => path !== filePath)
        : [...prev, filePath]
    );
  };

  const handleSelectAll = () => {
    if (selectedFiles.length === searchResults?.results?.length) {
      setSelectedFiles([]);
    } else {
      setSelectedFiles(searchResults?.results?.map((file: FileItem) => file.path) || []);
    }
  };

  const clearFilters = () => {
    setCategoryFilter('all');
    setSizeFilter('all');
    setDateFilter('all');
    setShowHidden(false);
    setSearchQuery('');
  };

  const files = searchResults?.results || [];
  const totalFiles = searchResults?.count || 0;
  const totalPages = Math.ceil(totalFiles / itemsPerPage);

  // Handle file actions
  const handleDeleteFiles = async () => {
    if (selectedFiles.length === 0) return;
    
    try {
      // API call to delete files would go here
      enqueueSnackbar(t('notifications.errorOccurred', { error: 'Delete API not implemented' }), { variant: 'warning' });
      setDeleteDialogOpen(false);
      setSelectedFiles([]);
    } catch (error) {
      enqueueSnackbar(t('notifications.errorOccurred', { error: error }), { variant: 'error' });
    }
  };

  const handleAnalyzeFile = async (filePath: string) => {
    try {
      await axios.post('/analyze', { filePath, analysisType: 'smart' });
      enqueueSnackbar(t('fileExplorer.actions.analyze') + ' ' + t('common.success'), { variant: 'success' });
    } catch (error) {
      enqueueSnackbar(t('notifications.errorOccurred', { error: error }), { variant: 'error' });
    }
  };

  const dateLocale = i18n.language === 'ko' ? ko : enUS;

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          {t('fileExplorer.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<NewFolderIcon />}
            onClick={() => enqueueSnackbar(t('common.info') + ': Feature coming soon', { variant: 'info' })}
          >
            {t('fileExplorer.actions.newFolder')}
          </Button>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
          >
            {t('fileExplorer.actions.upload')}
          </Button>
        </Box>
      </Box>

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder={t('fileExplorer.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    refetch();
                  }
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                  endAdornment: searchQuery && (
                    <InputAdornment position="end">
                      <IconButton size="small" onClick={() => setSearchQuery('')}>
                        <ClearIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Button
                  variant="outlined"
                  startIcon={<FilterIcon />}
                  onClick={() => setFilterOpen(!filterOpen)}
                >
                  Filters
                </Button>
                <IconButton
                  onClick={() => setViewMode(viewMode === 'list' ? 'grid' : 'list')}
                >
                  {viewMode === 'list' ? <GridViewIcon /> : <ListViewIcon />}
                </IconButton>
                {selectedFiles.length > 0 && (
                  <Button
                    variant="outlined"
                    onClick={() => setActionMenuAnchor(document.body)}
                  >
                    Actions ({selectedFiles.length})
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>

          {/* Active Filters */}
          {(categoryFilter !== 'all' || sizeFilter !== 'all' || dateFilter !== 'all') && (
            <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {categoryFilter !== 'all' && (
                <Chip
                  label={`Category: ${categoryFilter}`}
                  onDelete={() => setCategoryFilter('all')}
                  color="primary"
                  variant="outlined"
                />
              )}
              {sizeFilter !== 'all' && (
                <Chip
                  label={`Size: ${sizeFilter}`}
                  onDelete={() => setSizeFilter('all')}
                  color="primary"
                  variant="outlined"
                />
              )}
              {dateFilter !== 'all' && (
                <Chip
                  label={`Date: ${dateFilter}`}
                  onDelete={() => setDateFilter('all')}
                  color="primary"
                  variant="outlined"
                />
              )}
              <Button size="small" onClick={clearFilters}>
                Clear All
              </Button>
            </Box>
          )}

          {/* Filter Panel */}
          {filterOpen && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={categoryFilter}
                      label="Category"
                      onChange={(e) => setCategoryFilter(e.target.value)}
                    >
                      <MenuItem value="all">All Categories</MenuItem>
                      <MenuItem value="document">Documents</MenuItem>
                      <MenuItem value="image">Images</MenuItem>
                      <MenuItem value="video">Videos</MenuItem>
                      <MenuItem value="audio">Audio</MenuItem>
                      <MenuItem value="code">Code</MenuItem>
                      <MenuItem value="archive">Archives</MenuItem>
                      <MenuItem value="other">Other</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Size</InputLabel>
                    <Select
                      value={sizeFilter}
                      label="Size"
                      onChange={(e) => setSizeFilter(e.target.value)}
                    >
                      <MenuItem value="all">All Sizes</MenuItem>
                      <MenuItem value="small">Small (&lt; 1MB)</MenuItem>
                      <MenuItem value="medium">Medium (1-10MB)</MenuItem>
                      <MenuItem value="large">Large (&gt; 10MB)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Modified</InputLabel>
                    <Select
                      value={dateFilter}
                      label="Modified"
                      onChange={(e) => setDateFilter(e.target.value)}
                    >
                      <MenuItem value="all">Any Time</MenuItem>
                      <MenuItem value="today">Today</MenuItem>
                      <MenuItem value="week">This Week</MenuItem>
                      <MenuItem value="month">This Month</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showHidden}
                        onChange={(e) => setShowHidden(e.target.checked)}
                      />
                    }
                    label="Show Hidden"
                  />
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* File List */}
      <Card>
        <CardContent>
          {/* List Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Checkbox
                checked={selectedFiles.length === files.length && files.length > 0}
                indeterminate={selectedFiles.length > 0 && selectedFiles.length < files.length}
                onChange={handleSelectAll}
              />
              <Typography variant="body2" color="text.secondary">
                {totalFiles.toLocaleString()} files found
              </Typography>
            </Box>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Sort by</InputLabel>
              <Select
                value={sortBy}
                label="Sort by"
                onChange={(e) => setSortBy(e.target.value)}
              >
                <MenuItem value="modified">Modified</MenuItem>
                <MenuItem value="name">Name</MenuItem>
                <MenuItem value="size">Size</MenuItem>
                <MenuItem value="type">Type</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* File Items */}
          {searchLoading ? (
            <Box>
              {Array.from({ length: 10 }).map((_, index) => (
                <Skeleton key={index} height={60} sx={{ mb: 1 }} />
              ))}
            </Box>
          ) : (
            <List>
              {files.map((file: FileItem) => (
                <ListItem
                  key={file.path}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    '&:hover': { bgcolor: 'action.hover' },
                  }}
                >
                  <Checkbox
                    checked={selectedFiles.includes(file.path)}
                    onChange={() => handleSelectFile(file.path)}
                  />
                  <ListItemIcon>
                    {getFileIcon(file.metadata.category)}
                  </ListItemIcon>
                  <ListItemText
                    primary={file.name}
                    secondary={
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Typography variant="caption">
                          {formatBytes(file.size)}
                        </Typography>
                        <Typography variant="caption">
                          {formatDistanceToNow(new Date(file.modified * 1000), { addSuffix: true })}
                        </Typography>
                        <Chip
                          label={file.metadata.category}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      onClick={(e) => setActionMenuAnchor(e.currentTarget)}
                    >
                      <MoreIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={(e, page) => setCurrentPage(page)}
                color="primary"
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Upload Files</DialogTitle>
        <DialogContent>
          <Box
            {...getRootProps()}
            sx={{
              border: 2,
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderStyle: 'dashed',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'transparent',
            }}
          >
            <input {...getInputProps()} />
            <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              or click to select files
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Action Menu */}
      <Menu
        anchorEl={actionMenuAnchor}
        open={Boolean(actionMenuAnchor)}
        onClose={() => setActionMenuAnchor(null)}
      >
        <MenuItem onClick={() => {/* Handle download */}}>
          <ListItemIcon><DownloadIcon /></ListItemIcon>
          Download
        </MenuItem>
        <MenuItem onClick={() => {/* Handle share */}}>
          <ListItemIcon><ShareIcon /></ListItemIcon>
          Share
        </MenuItem>
        <MenuItem onClick={() => {/* Handle delete */}}>
          <ListItemIcon><DeleteIcon /></ListItemIcon>
          Delete
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default FileExplorer;