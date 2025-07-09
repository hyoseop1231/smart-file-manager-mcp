# Smart File Manager Web UI

Modern, responsive web interface for monitoring and controlling the Smart File Manager AI system.

## 🎯 Features

### 📊 **Dashboard**
- Real-time system health monitoring
- File distribution analytics with interactive charts
- Performance metrics visualization
- Recent file activity tracking
- Service status indicators

### 🗂️ **File Explorer**
- Advanced search with natural language queries
- Multiple view modes (list/grid)
- Smart filtering by category, size, date
- Drag-and-drop file upload
- Batch file operations
- Real-time file indexing

### 📈 **Analytics**
- Duplicate file detection with multiple methods
- Storage usage analysis
- System performance trends
- File activity patterns
- Potential savings calculator

### 🤖 **AI Organization**
- Step-by-step organization wizard
- Preview mode before actual organization
- Multiple organization methods (content, date, type)
- AI-powered file categorization
- Real-time progress tracking

### ⚙️ **Settings**
- Storage management configuration
- Performance tuning options
- AI/LLM model selection
- Automated task scheduling
- Notification preferences
- Security settings

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Smart File Manager API running on port 8001

### Installation

```bash
# Install dependencies
cd web-ui
npm install

# Start development server
npm start
```

The application will open at `http://localhost:3000` and automatically proxy API requests to `http://localhost:8001`.

### Production Build

```bash
# Create optimized production build
npm run build

# Serve the build folder
npx serve -s build -l 3000
```

## 🏗️ Architecture

### Technology Stack
- **React 18** with TypeScript
- **Material-UI (MUI)** for components and theming
- **React Query** for data fetching and caching
- **Recharts** for data visualization
- **React Router** for navigation
- **Axios** for API communication

### Component Structure
```
src/
├── components/
│   └── Layout/          # Main application layout
├── pages/
│   ├── Dashboard/       # System overview and metrics
│   ├── FileExplorer/    # File browsing and search
│   ├── Analytics/       # Data analytics and insights
│   ├── Organization/    # AI-powered file organization
│   └── Settings/        # System configuration
├── App.tsx             # Main application component
└── index.tsx           # Application entry point
```

### API Integration
The UI communicates with the Smart File Manager API endpoints:

- `GET /health` - System health and status
- `GET /metrics` - Detailed performance metrics
- `POST /search` - File search with AI enhancement
- `POST /organize` - File organization operations
- `POST /duplicates` - Duplicate file detection
- `POST /analyze` - Individual file analysis
- `GET /recent` - Recent file activity

## 🎨 Design System

### Color Palette
- **Primary**: Blue (#1976D2) - Navigation, CTAs, primary actions
- **Secondary**: Teal (#00796B) - Success states, confirmations
- **Warning**: Orange (#FF6B35) - Warnings, potential actions
- **Background**: Light Gray (#FAFAFA) - Application background
- **Surface**: White (#FFFFFF) - Card backgrounds

### Typography
- **Headers**: Roboto 600 weight, various sizes
- **Body**: Roboto 400 weight, 14-16px
- **Captions**: Roboto 400 weight, 12px

### Responsive Design
- **Desktop**: Full sidebar navigation, multi-column layouts
- **Tablet**: Collapsible sidebar, adapted layouts
- **Mobile**: Bottom navigation, single-column layouts

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the web-ui directory:

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8001

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_AI_FEATURES=true

# Development
REACT_APP_DEBUG_MODE=false
```

### Proxy Configuration
The development server proxies API requests to avoid CORS issues. This is configured in `package.json`:

```json
{
  "proxy": "http://localhost:8001"
}
```

## 📱 User Experience

### Key Workflows

1. **File Search & Discovery**
   - Natural language search queries
   - Advanced filtering options
   - Real-time results
   - Preview and download

2. **AI-Powered Organization**
   - Select source directory
   - Choose organization method
   - Preview changes
   - Execute with progress tracking

3. **System Monitoring**
   - Real-time dashboard updates
   - Performance trend analysis
   - Issue detection and alerts
   - Resource usage tracking

4. **Duplicate Management**
   - Multiple detection methods
   - Visual duplicate grouping
   - Bulk resolution actions
   - Savings calculation

### Accessibility Features
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- Focus indicators
- Alternative text for icons

## 🚀 Performance Optimizations

### Loading Strategies
- Skeleton screens during initial load
- Progressive data loading
- Image lazy loading
- Optimistic UI updates

### Caching
- React Query for API response caching
- Component memoization
- Static asset caching
- Service worker for offline support

### Bundle Optimization
- Code splitting by route
- Tree shaking for unused code
- Compression and minification
- CDN delivery for fonts and icons

## 🧪 Testing

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

## 🔧 Development

### Available Scripts
- `npm start` - Development server with hot reload
- `npm run build` - Production build
- `npm test` - Run test suite
- `npm run eject` - Eject from Create React App

### Adding New Features
1. Create component in appropriate directory
2. Add route to App.tsx if needed
3. Implement API integration with React Query
4. Add proper TypeScript types
5. Include error handling and loading states
6. Add tests for critical functionality

## 📦 Deployment

### Docker Deployment
```bash
# Build Docker image
docker build -t smart-file-manager-ui .

# Run container
docker run -p 3000:80 smart-file-manager-ui
```

### Static Hosting
The built application is a static single-page application that can be deployed to:
- Nginx/Apache web servers
- AWS S3 + CloudFront
- Vercel/Netlify
- GitHub Pages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## 📄 License

This project is part of the Smart File Manager system and follows the same licensing terms.

---

For more information about the Smart File Manager system, see the main project README.