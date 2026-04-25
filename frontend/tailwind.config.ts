import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0F1117',
          secondary: '#1A1D27',
          card: '#1E2130',
        },
        border: {
          DEFAULT: 'rgba(255,255,255,0.08)',
          strong: 'rgba(255,255,255,0.15)',
        },
        text: {
          primary: '#E8E9ED',
          secondary: '#8B8FA8',
          muted: '#5A5E72',
        },
        accent: {
          blue: '#0070F2',
          'blue-hover': '#005ED4',
        },
        success: '#1E8C4E',
        warning: '#E76500',
        danger: '#BB0000',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'width-expand': 'widthExpand 0.8s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        widthExpand: {
          from: { width: '0%' },
          to: { width: 'var(--target-width)' },
        },
      },
    },
  },
  plugins: [],
}

export default config
