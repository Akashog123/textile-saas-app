/**
 * SE Textile App - Theme Configuration
 * Centralized theme management based on navbar blue color scheme
 */

// Theme configuration object
export const themeConfig = {
  // Primary color palette (based on navbar)
  colors: {
    primary: '#4A90E2',
    primaryDark: '#357ABD',
    primaryLight: '#6BA3E5',
    accent: '#B3D9FF',
    accentLight: '#D4E9FF',
    
    // Background colors
    bg: '#F0F4F8',
    bgAlt: '#E6F2FF',
    bgLight: '#F8FAFC',
    bgWhite: '#FFFFFF',
    
    // Text colors
    textDark: '#2C3E50',
    textMuted: '#7F8C8D',
    textLight: '#95A5A6',
    
    // Semantic colors
    success: '#10B981',
    successDark: '#059669',
    warning: '#F59E0B',
    warningDark: '#D97706',
    danger: '#EF4444',
    dangerDark: '#DC2626',
    info: '#3B82F6',
    infoDark: '#2563EB',
    
    // Border and shadow
    border: '#E5E7EB',
    borderLight: '#F3F4F6',
    shadow: 'rgba(0, 0, 0, 0.1)',
    shadowLight: 'rgba(0, 0, 0, 0.05)',
    
    // Glass effect colors
    glassBg: 'rgba(255, 255, 255, 0.8)',
    glassBorder: 'rgba(74, 144, 226, 0.2)',
    glassShadow: 'rgba(0, 0, 0, 0.03)'
  },
  
  // Gradients
  gradients: {
    primary: 'linear-gradient(135deg, #4A90E2 0%, #357ABD 100%)',
    accent: 'linear-gradient(135deg, #B3D9FF 0%, #6BA3E5 100%)',
    background: 'linear-gradient(135deg, #F0F4F8 0%, #E6F2FF 100%)',
    hero: 'linear-gradient(135deg, rgba(74, 144, 226, 0.1) 0%, rgba(179, 217, 255, 0.05) 100%)',
    success: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
    warning: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
    danger: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
    info: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)'
  },
  
  // Typography
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem'
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75
    }
  },
  
  // Spacing
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem'
  },
  
  // Border radius
  borderRadius: {
    none: '0',
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    '2xl': '1.5rem',
    full: '9999px'
  },
  
  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
    glass: '0 4px 30px rgba(0, 0, 0, 0.03)',
    hover: '0 8px 40px rgba(74, 144, 226, 0.15)'
  },
  
  // Transitions
  transitions: {
    fast: '0.15s ease',
    normal: '0.3s ease',
    slow: '0.5s ease',
    bounce: '0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
    smooth: '0.3s cubic-bezier(0.4, 0, 0.2, 1)'
  },
  
  // Z-index layers
  zIndex: {
    hide: -1,
    auto: 'auto',
    base: 0,
    docked: 10,
    dropdown: 1000,
    sticky: 1100,
    banner: 1200,
    overlay: 1300,
    modal: 1400,
    popover: 1500,
    skipLink: 1600,
    toast: 1700,
    tooltip: 1800
  },
  
  // Breakpoints
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px'
  },
  
  // Component-specific configurations
  components: {
    button: {
      padding: {
        sm: '0.5rem 1rem',
        md: '0.75rem 1.5rem',
        lg: '1rem 2rem'
      },
      borderRadius: '12px',
      fontWeight: 600,
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
    },
    card: {
      borderRadius: '16px',
      padding: '2rem',
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(74, 144, 226, 0.1)',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
    },
    input: {
      borderRadius: '12px',
      padding: '0.75rem 1rem',
      fontSize: '1rem',
      border: '1px solid #E5E7EB',
      background: 'rgba(255, 255, 255, 0.8)',
      transition: 'all 0.3s ease'
    },
    navbar: {
      height: '80px',
      background: 'rgba(255, 255, 255, 0.8)',
      backdropFilter: 'blur(16px) saturate(180%)',
      borderBottom: '1px solid rgba(74, 144, 226, 0.2)',
      boxShadow: '0 4px 30px rgba(0, 0, 0, 0.03)'
    }
  }
};

// CSS custom properties generator
export const generateCSSVariables = (config = themeConfig) => {
  const cssVars = {};
  
  // Color variables
  Object.entries(config.colors).forEach(([key, value]) => {
    cssVars[`--color-${key}`] = value;
  });
  
  // Gradient variables
  Object.entries(config.gradients).forEach(([key, value]) => {
    cssVars[`--gradient-${key}`] = value;
  });
  
  // Typography variables
  Object.entries(config.typography.fontSize).forEach(([key, value]) => {
    cssVars[`--font-size-${key}`] = value;
  });
  
  Object.entries(config.typography.fontWeight).forEach(([key, value]) => {
    cssVars[`--font-weight-${key}`] = value;
  });
  
  // Spacing variables
  Object.entries(config.spacing).forEach(([key, value]) => {
    cssVars[`--spacing-${key}`] = value;
  });
  
  // Border radius variables
  Object.entries(config.borderRadius).forEach(([key, value]) => {
    cssVars[`--radius-${key}`] = value;
  });
  
  // Shadow variables
  Object.entries(config.shadows).forEach(([key, value]) => {
    cssVars[`--shadow-${key}`] = value;
  });
  
  // Transition variables
  Object.entries(config.transitions).forEach(([key, value]) => {
    cssVars[`--transition-${key}`] = value;
  });
  
  // Z-index variables
  Object.entries(config.zIndex).forEach(([key, value]) => {
    cssVars[`--z-${key}`] = value;
  });
  
  return cssVars;
};

// Apply theme to document root
export const applyTheme = (config = themeConfig) => {
  const root = document.documentElement;
  const cssVars = generateCSSVariables(config);
  
  Object.entries(cssVars).forEach(([property, value]) => {
    root.style.setProperty(property, value);
  });
};

// Theme utilities
export const themeUtils = {
  // Get color with opacity
  getColor: (colorName, opacity = 1) => {
    const color = themeConfig.colors[colorName];
    if (!color) return colorName;
    
    if (opacity < 1) {
      // Convert hex to rgba
      const hex = color.replace('#', '');
      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);
      return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }
    
    return color;
  },
  
  // Get responsive value
  getResponsive: (values, breakpoint = 'md') => {
    if (typeof values === 'object') {
      return values[breakpoint] || values.md || values.base;
    }
    return values;
  },
  
  // Create gradient
  createGradient: (colors, direction = '135deg') => {
    const colorStops = colors.map((color, index) => {
      const position = (index / (colors.length - 1)) * 100;
      return `${color} ${position}%`;
    }).join(', ');
    
    return `linear-gradient(${direction}, ${colorStops})`;
  },
  
  // Get theme-aware shadow
  getShadow: (type = 'md', color = null) => {
    const baseShadow = themeConfig.shadows[type] || themeConfig.shadows.md;
    
    if (color) {
      // Replace rgba colors with theme color
      return baseShadow.replace(/rgba\([^)]+\)/g, themeUtils.getColor(color, 0.1));
    }
    
    return baseShadow;
  }
};

// Export default theme
export default themeConfig;
