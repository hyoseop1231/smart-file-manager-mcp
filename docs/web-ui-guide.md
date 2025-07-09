# Smart File Manager Web UI Guide

The Smart File Manager includes a modern, responsive web interface for monitoring and controlling your file management system.

## Features Overview

### 📊 Dashboard
Real-time system monitoring with interactive visualizations:
- **System Metrics**: CPU, Memory, and Disk usage charts
- **File Activity**: Timeline of recent file operations
- **Quick Stats**: Total files, storage usage, recent activity
- **Health Status**: Service status indicators

### 🗂️ File Explorer
Advanced file browsing and search capabilities:
- **Natural Language Search**: Use conversational queries
- **Filter Options**: By type, size, date, location
- **Batch Operations**: Select multiple files for actions
- **Preview**: Quick file information display
- **Sort & View**: Multiple viewing options

### 📈 Analytics
Insights and optimization tools:
- **Duplicate Detection**: Find and manage duplicate files
- **Storage Analysis**: Visualize space usage patterns
- **File Distribution**: Charts by type, size, age
- **Performance Metrics**: System performance trends
- **Potential Savings**: Calculate reclaimable space

### 🤖 Organization
AI-powered file organization wizard:
- **Smart Categorization**: AI analyzes and suggests organization
- **Dry Run Mode**: Preview changes before applying
- **Custom Rules**: Define your organization preferences
- **Progress Tracking**: Real-time organization status
- **Undo Support**: Rollback changes if needed

### ⚙️ Settings
System configuration and management:
- **Directory Management**: Add/remove watched directories
- **Indexing Schedule**: Configure scan intervals
- **AI Model Selection**: Choose LLM models
- **Performance Tuning**: Adjust system resources
- **Export/Import**: Backup configurations

## Accessing the Web UI

### Development Mode
For hot-reload during development:
```bash
./start-webui.sh
```
Access at: http://localhost:3002

### Production Mode
Using Docker Compose:
```bash
docker-compose up -d web-ui
```
Access at: http://localhost:3002

### Direct npm (Development)
```bash
cd web-ui
npm install
PORT=3002 npm start
```

## User Interface Guide

### Navigation
- **Sidebar**: Main navigation between features
- **Header**: Search bar and user actions
- **Content Area**: Feature-specific interface

### Common Actions

#### Searching Files
1. Click on "File Explorer" in sidebar
2. Use the search bar at the top
3. Apply filters as needed
4. Click on files for details

#### Finding Duplicates
1. Navigate to "Analytics"
2. Select duplicate detection method
3. Set minimum file size
4. Review and manage duplicates

#### Organizing Files
1. Go to "Organization"
2. Select source directory
3. Choose organization method
4. Preview results
5. Apply changes

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Focus search |
| `Ctrl/Cmd + /` | Toggle sidebar |
| `Esc` | Close dialogs |
| `F5` | Refresh data |

## API Integration

The Web UI communicates with the backend API:

### Base URL Configuration
Set in environment:
```bash
REACT_APP_API_URL=http://localhost:8001
```

### API Endpoints Used
- `/health` - System health check
- `/metrics` - Performance metrics
- `/search` - File search
- `/organize` - File organization
- `/duplicates` - Duplicate detection
- `/recent` - Recent files
- `/task/{id}` - Task status

## Customization

### Theme Customization
Edit `src/theme.ts`:
```typescript
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    // Customize colors
  },
});
```

### Adding Custom Pages
1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Update navigation in `src/components/Layout/`

### Custom Widgets
Add to dashboard in `src/pages/Dashboard/Dashboard.tsx`

## Performance Optimization

### Data Fetching
- Uses React Query for caching
- Automatic background refetch
- Optimistic updates

### Large File Lists
- Virtual scrolling for performance
- Pagination support
- Lazy loading

### Real-time Updates
- Polling intervals configurable
- WebSocket support (planned)

## Troubleshooting

### UI Not Loading

1. **Check API connection**:
   ```bash
   curl http://localhost:8001/health
   ```

2. **Verify port availability**:
   ```bash
   lsof -i :3002
   ```

3. **Check browser console** for errors

### Slow Performance

1. **Reduce fetch intervals** in components
2. **Enable production build**:
   ```bash
   npm run build
   npm install -g serve
   serve -s build -p 3002
   ```

3. **Check API response times**

### CORS Issues

Ensure API allows frontend origin:
```python
# In FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Browser Compatibility

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 90+ | ✅ Full |
| Firefox | 88+ | ✅ Full |
| Safari | 14+ | ✅ Full |
| Edge | 90+ | ✅ Full |
| IE | All | ❌ Not Supported |

## Mobile Responsiveness

The UI is fully responsive:
- **Desktop**: Full features with sidebar
- **Tablet**: Collapsible sidebar
- **Mobile**: Bottom navigation

## Security Considerations

1. **Authentication**: Currently no auth (local use)
2. **HTTPS**: Recommended for production
3. **API Keys**: Store securely in environment
4. **File Access**: Read-only by default

## Future Enhancements

### Planned Features
- [ ] Dark mode toggle
- [ ] Multi-language support
- [ ] File preview (images, PDFs)
- [ ] Drag-and-drop upload
- [ ] Real-time notifications
- [ ] User preferences persistence
- [ ] Export reports

### Community Requests
Submit feature requests at:
https://github.com/hyoseop1231/smart-file-manager-mcp/issues

---

For more information, visit the project repository.