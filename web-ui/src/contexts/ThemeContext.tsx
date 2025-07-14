import React, { createContext, useContext, useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { PaletteMode } from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';

interface ThemeContextType {
  mode: PaletteMode;
  toggleColorMode: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ColorModeProviderProps {
  children: React.ReactNode;
}

export const ColorModeProvider: React.FC<ColorModeProviderProps> = ({ children }) => {
  const [mode, setMode] = useState<PaletteMode>(() => {
    const savedMode = localStorage.getItem('themeMode');
    return (savedMode as PaletteMode) || 'light';
  });

  useEffect(() => {
    localStorage.setItem('themeMode', mode);
  }, [mode]);

  const toggleColorMode = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  const theme = React.useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          ...(mode === 'light'
            ? {
                // Light mode colors
                primary: {
                  main: '#1976D2',
                  light: '#42A5F5',
                  dark: '#1565C0',
                },
                secondary: {
                  main: '#00796B',
                  light: '#4DB6AC',
                  dark: '#00695C',
                },
                error: {
                  main: '#D32F2F',
                },
                warning: {
                  main: '#FF6B35',
                },
                info: {
                  main: '#0288D1',
                },
                success: {
                  main: '#2E7D32',
                },
                background: {
                  default: '#FAFAFA',
                  paper: '#FFFFFF',
                },
              }
            : {
                // Dark mode colors
                primary: {
                  main: '#90CAF9',
                  light: '#E3F2FD',
                  dark: '#42A5F5',
                },
                secondary: {
                  main: '#80CBC4',
                  light: '#B2DFDB',
                  dark: '#4DB6AC',
                },
                error: {
                  main: '#F44336',
                },
                warning: {
                  main: '#FF8A65',
                },
                info: {
                  main: '#29B6F6',
                },
                success: {
                  main: '#66BB6A',
                },
                background: {
                  default: '#121212',
                  paper: '#1E1E1E',
                },
              }),
        },
        typography: {
          fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
          h1: {
            fontSize: '2rem',
            fontWeight: 600,
          },
          h2: {
            fontSize: '1.5rem',
            fontWeight: 600,
          },
          h3: {
            fontSize: '1.25rem',
            fontWeight: 500,
          },
          body1: {
            fontSize: '1rem',
            lineHeight: 1.5,
          },
          body2: {
            fontSize: '0.875rem',
            lineHeight: 1.43,
          },
        },
        shape: {
          borderRadius: 8,
        },
        spacing: 8,
        components: {
          MuiCard: {
            styleOverrides: {
              root: {
                boxShadow: mode === 'light' 
                  ? '0px 2px 4px rgba(0, 0, 0, 0.1)'
                  : '0px 2px 4px rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
              },
            },
          },
          MuiButton: {
            styleOverrides: {
              root: {
                textTransform: 'none',
                borderRadius: '6px',
              },
            },
          },
        },
      }),
    [mode],
  );

  return (
    <ThemeContext.Provider value={{ mode, toggleColorMode }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};