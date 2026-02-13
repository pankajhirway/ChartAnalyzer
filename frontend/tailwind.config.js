/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        surface: {
          DEFAULT: '#0b0f19',
          50: '#f8fafc',
          100: '#1e293b',
          200: '#172032',
          300: '#111827',
          400: '#0f172a',
          500: '#0b0f19',
        },
        bullish: {
          50: 'rgba(16, 185, 129, 0.08)',
          100: 'rgba(16, 185, 129, 0.15)',
          200: 'rgba(16, 185, 129, 0.25)',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
        },
        bearish: {
          50: 'rgba(239, 68, 68, 0.08)',
          100: 'rgba(239, 68, 68, 0.15)',
          200: 'rgba(239, 68, 68, 0.25)',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        neutral: {
          50: 'rgba(148, 163, 184, 0.06)',
          100: 'rgba(148, 163, 184, 0.1)',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
        },
      },
      borderRadius: {
        xl: '12px',
        '2xl': '16px',
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'fade-in': 'fadeIn 0.3s ease forwards',
        'slide-down': 'slideDown 0.2s cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeInUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        slideDown: {
          from: { opacity: '0', transform: 'translateY(-8px) scale(0.98)' },
          to:   { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.7' },
        },
      },
    },
  },
  plugins: [],
}
