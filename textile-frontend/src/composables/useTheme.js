/**
 * SE Textile App - Theme Composable
 * Easy theme management and utilities
 */

import { ref, onMounted, watch } from 'vue';
import themeConfig, { applyTheme, themeUtils } from '@/styles/theme-config';

// Theme state
const currentTheme = ref('light');
const isDarkMode = ref(false);

// Theme composable
export function useTheme() {
  
  // Apply theme on mount
  onMounted(() => {
    applyTheme();
    detectSystemTheme();
  });
  
  // Detect system theme preference
  const detectSystemTheme = () => {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      isDarkMode.value = true;
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      isDarkMode.value = e.matches;
    });
  };
  
  // Toggle dark mode (future feature)
  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value;
    // Dark mode implementation can be added here
    console.log('Dark mode toggled:', isDarkMode.value);
  };
  
  // Get theme-aware color
  const getColor = (colorName, opacity = 1) => {
    return themeUtils.getColor(colorName, opacity);
  };
  
  // Get theme gradient
  const getGradient = (gradientName) => {
    return themeConfig.gradients[gradientName] || themeConfig.gradients.primary;
  };
  
  // Get theme shadow
  const getShadow = (shadowName = 'md') => {
    return themeConfig.shadows[shadowName] || themeConfig.shadows.md;
  };
  
  // Get responsive spacing
  const getSpacing = (spacingName) => {
    return themeConfig.spacing[spacingName] || themeConfig.spacing.md;
  };
  
  // Get responsive font size
  const getFontSize = (sizeName) => {
    return themeConfig.typography.fontSize[sizeName] || themeConfig.typography.fontSize.base;
  };
  
  // Get border radius
  const getBorderRadius = (radiusName) => {
    return themeConfig.borderRadius[radiusName] || themeConfig.borderRadius.md;
  };
  
  // Get transition
  const getTransition = (transitionName = 'normal') => {
    return themeConfig.transitions[transitionName] || themeConfig.transitions.normal;
  };
  
  // Component-specific styles
  const getButtonStyles = (variant = 'primary', size = 'md') => {
    const baseStyles = {
      padding: themeConfig.components.button.padding[size],
      borderRadius: themeConfig.components.button.borderRadius,
      fontWeight: themeConfig.components.button.fontWeight,
      transition: themeConfig.components.button.transition
    };
    
    const variantStyles = {
      primary: {
        background: themeConfig.gradients.primary,
        color: '#ffffff',
        border: 'none',
        boxShadow: themeConfig.shadows.sm
      },
      outline: {
        background: 'transparent',
        color: themeConfig.colors.primary,
        border: `2px solid ${themeConfig.colors.primary}`,
        boxShadow: 'none'
      },
      secondary: {
        background: themeConfig.colors.bgLight,
        color: themeConfig.colors.textDark,
        border: `1px solid ${themeConfig.colors.border}`,
        boxShadow: 'none'
      }
    };
    
    return { ...baseStyles, ...variantStyles[variant] };
  };
  
  const getCardStyles = () => {
    return themeConfig.components.card;
  };
  
  const getInputStyles = () => {
    return themeConfig.components.input;
  };
  
  // Utility functions
  const createResponsiveStyle = (property, values) => {
    const breakpoints = themeConfig.breakpoints;
    let style = {};
    
    Object.entries(values).forEach(([breakpoint, value]) => {
      if (breakpoint === 'base') {
        style[property] = value;
      } else {
        const mediaQuery = `@media (min-width: ${breakpoints[breakpoint]})`;
        style[mediaQuery] = {
          [property]: value
        };
      }
    });
    
    return style;
  };
  
  const createGradientClass = (colors, direction = '135deg') => {
    return `linear-gradient(${direction}, ${colors.join(', ')})`;
  };
  
  // CSS class generators
  const getTextClass = (colorName, weight = 'normal') => {
    const color = themeConfig.colors[colorName] || colorName;
    const fontWeight = themeConfig.typography.fontWeight[weight] || weight;
    
    return {
      color: color,
      fontWeight: fontWeight
    };
  };
  
  const getBackgroundClass = (colorName) => {
    const color = themeConfig.colors[colorName] || colorName;
    return {
      backgroundColor: color
    };
  };
  
  const getBorderClass = (colorName, width = '1px', style = 'solid') => {
    const color = themeConfig.colors[colorName] || colorName;
    return {
      border: `${width} ${style} ${color}`
    };
  };
  
  // Watch for theme changes
  watch(isDarkMode, (newValue) => {
    // Apply dark mode styles when implemented
    document.documentElement.classList.toggle('dark-mode', newValue);
  });
  
  return {
    // State
    currentTheme,
    isDarkMode,
    
    // Actions
    toggleDarkMode,
    
    // Utilities
    getColor,
    getGradient,
    getShadow,
    getSpacing,
    getFontSize,
    getBorderRadius,
    getTransition,
    
    // Component styles
    getButtonStyles,
    getCardStyles,
    getInputStyles,
    
    // Advanced utilities
    createResponsiveStyle,
    createGradientClass,
    getTextClass,
    getBackgroundClass,
    getBorderClass,
    
    // Raw config access
    themeConfig,
    themeUtils
  };
}

// Export individual utilities for non-composable usage
export { themeConfig, themeUtils, applyTheme };

// Export default
export default useTheme;
