import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

const DEFAULT_THEME = {
  // Primary brand colors
  primary: '#3B82F6', // Blue
  primaryDark: '#2563EB',
  primaryLight: '#60A5FA',
  
  // Secondary colors
  secondary: '#10B981', // Green
  secondaryDark: '#059669',
  secondaryLight: '#34D399',
  
  // Accent colors
  accent: '#8B5CF6', // Purple
  accentDark: '#7C3AED',
  accentLight: '#A78BFA',
  
  // Status colors
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  
  // Neutral colors
  background: '#FFFFFF',
  surface: '#F9FAFB',
  border: '#E5E7EB',
  text: '#111827',
  textSecondary: '#6B7280',
  
  // Logo
  logo: null, // Will be set by user
  logoUrl: '/logo.svg', // Default logo path
  
  // Mode
  mode: 'light', // 'light' or 'dark'
};

const DARK_THEME = {
  ...DEFAULT_THEME,
  background: '#111827',
  surface: '#1F2937',
  border: '#374151',
  text: '#F9FAFB',
  textSecondary: '#9CA3AF',
  mode: 'dark',
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    // Load theme from localStorage
    const saved = localStorage.getItem('dashboard-theme');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse saved theme:', e);
      }
    }
    return DEFAULT_THEME;
  });

  // Save theme to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('dashboard-theme', JSON.stringify(theme));
    
    // Apply CSS variables to document root
    const root = document.documentElement;
    Object.entries(theme).forEach(([key, value]) => {
      if (typeof value === 'string' && value.startsWith('#')) {
        root.style.setProperty(`--theme-${key}`, value);
      }
    });
    
    // Apply dark/light mode class
    if (theme.mode === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
  }, [theme]);

  const updateTheme = (updates) => {
    setTheme(prev => ({ ...prev, ...updates }));
  };

  const resetTheme = () => {
    setTheme(DEFAULT_THEME);
  };

  const toggleMode = () => {
    setTheme(prev => ({
      ...(prev.mode === 'light' ? DARK_THEME : DEFAULT_THEME),
      // Preserve custom colors and logo
      ...(prev.logo && { logo: prev.logo, logoUrl: prev.logoUrl }),
    }));
  };

  const uploadLogo = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const logoData = e.target.result;
        setTheme(prev => ({
          ...prev,
          logo: file.name,
          logoUrl: logoData,
        }));
        resolve(logoData);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const value = {
    theme,
    updateTheme,
    resetTheme,
    toggleMode,
    uploadLogo,
    isDark: theme.mode === 'dark',
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

export { DEFAULT_THEME, DARK_THEME };

