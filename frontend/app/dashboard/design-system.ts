// KEOTrading Design System - Based on UI/UX Pro Max
// Styles: Dark Mode (OLED) + Data-Dense Dashboard + Real-Time Monitoring

export const tokens = {
  // Colors - Trading Platform Dark Theme
  colors: {
    // Base
    background: '#0A0A0F',      // Deep OLED black
    backgroundSecondary: '#12121A', // Card backgrounds
    backgroundTertiary: '#1A1A24', // Elevated surfaces
    
    // Borders
    border: '#2A2A3A',
    borderHover: '#3A3A4A',
    
    // Text
    foreground: '#FFFFFF',
    foregroundMuted: '#9CA3AF',
    foregroundSubtle: '#6B7280',
    
    // Primary - Electric Blue
    primary: '#3B82F6',
    primaryHover: '#60A5FA',
    primaryForeground: '#FFFFFF',
    
    // Accent - Cyan
    accent: '#06B6D4',
    accentHover: '#22D3EE',
    
    // Success - Trading Green
    success: '#10B981',
    successLight: '#34D399',
    successBg: 'rgba(16, 185, 129, 0.1)',
    
    // Danger - Trading Red
    danger: '#EF4444',
    dangerLight: '#F87171',
    dangerBg: 'rgba(239, 68, 68, 0.1)',
    
    // Warning - Amber
    warning: '#F59E0B',
    warningLight: '#FBBF24',
    warningBg: 'rgba(245, 158, 11, 0.1)',
    
    // Purple - Special
    purple: '#8B5CF6',
    purpleLight: '#A78BFA',
    
    // Chart colors
    chart: {
      line1: '#3B82F6',  // Blue
      line2: '#10B981',  // Green
      line3: '#F59E0B',  // Amber
      line4: '#EF4444',  // Red
      line5: '#8B5CF6',  // Purple
      area: 'rgba(59, 130, 246, 0.1)',
    }
  },
  
  // Typography
  typography: {
    fontFamily: {
      sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      mono: '"JetBrains Mono", "Fira Code", monospace',
    },
    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',    // 14px
      base: '1rem',      // 16px
      lg: '1.125rem',    // 18px
      xl: '1.25rem',     // 20px
      '2xl': '1.5rem',   // 24px
      '3xl': '1.875rem', // 30px
      '4xl': '2.25rem',  // 36px
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
  
  // Spacing
  spacing: {
    0: '0',
    1: '0.25rem',   // 4px
    2: '0.5rem',    // 8px
    3: '0.75rem',   // 12px
    4: '1rem',      // 16px
    5: '1.25rem',   // 20px
    6: '1.5rem',    // 24px
    8: '2rem',      // 32px
    10: '2.5rem',   // 40px
    12: '3rem',     // 48px
  },
  
  // Border Radius
  radius: {
    none: '0',
    sm: '0.25rem',   // 4px
    md: '0.5rem',    // 8px
    lg: '0.75rem',   // 12px
    xl: '1rem',      // 16px
    '2xl': '1.5rem', // 24px
    full: '9999px',
  },
  
  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.4)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
    glow: {
      success: '0 0 20px rgba(16, 185, 129, 0.3)',
      danger: '0 0 20px rgba(239, 68, 68, 0.3)',
      primary: '0 0 20px rgba(59, 130, 246, 0.3)',
    }
  },
  
  // Transitions
  transitions: {
    fast: '150ms ease',
    normal: '200ms ease',
    slow: '300ms ease',
  },
  
  // Z-Index
  zIndex: {
    base: 0,
    dropdown: 50,
    sticky: 60,
    modal: 80,
    toast: 100,
    tooltip: 150,
  }
}

// Utility function for CSS variable generation
export function generateCSSVariables(): string {
  const vars: string[] = []
  
  // Colors
  Object.entries(tokens.colors).forEach(([key, value]) => {
    if (typeof value === 'object') {
      Object.entries(value).forEach(([subKey, subValue]) => {
        vars.push(`--color-${key}-${subKey}: ${subValue}`)
      })
    } else {
      vars.push(`--color-${key}: ${value}`)
    }
  })
  
  return vars.join('; ')
}
