import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { SnackbarProvider } from 'notistack';
import { I18nextProvider } from 'react-i18next';
import i18n from './i18n/i18n';
import './config/axios'; // Initialize axios configuration

import { ColorModeProvider } from './contexts/ThemeContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { FolderProvider } from './contexts/FolderContext';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import FileExplorer from './pages/FileExplorer/FileExplorer';
import Analytics from './pages/Analytics/Analytics';
import Organization from './pages/Organization/Organization';
import Settings from './pages/Settings/Settings';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <I18nextProvider i18n={i18n}>
      <QueryClientProvider client={queryClient}>
        <ColorModeProvider>
          <FolderProvider>
            <NotificationProvider>
              <SnackbarProvider 
                maxSnack={3}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'right',
                }}
              >
                <Router>
                  <Layout>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/explorer" element={<FileExplorer />} />
                      <Route path="/analytics" element={<Analytics />} />
                      <Route path="/organization" element={<Organization />} />
                      <Route path="/settings" element={<Settings />} />
                    </Routes>
                  </Layout>
                </Router>
              </SnackbarProvider>
            </NotificationProvider>
          </FolderProvider>
        </ColorModeProvider>
      </QueryClientProvider>
    </I18nextProvider>
  );
}

export default App;