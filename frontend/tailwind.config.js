/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Sora', 'Inter', 'sans-serif'],
        accent: ['Poppins', 'Inter', 'sans-serif'],
      },
      colors: {
        surface: {
          950: '#09090b',
          900: '#0f0f12',
          800: '#18181c',
          700: '#222228',
          600: '#2e2e36',
        },
        brand: {
          indigo: '#6366f1',
          cyan: '#22d3ee',
          glow: '#818cf8',
        },
      },
      boxShadow: {
        glow: '0 0 40px -10px rgba(99, 102, 241, 0.4)',
        'glow-sm': '0 0 20px -5px rgba(34, 211, 238, 0.3)',
        glass: '0 8px 32px rgba(0, 0, 0, 0.3)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
        float: 'float 6s ease-in-out infinite',
        shimmer: 'shimmer 1.5s infinite',
      },
      keyframes: {
        'pulse-soft': {
          '0%, 100%': { opacity: '0.6', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.05)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      opacity: {
        15: '0.15',
      },
    },
  },
  plugins: [],
}
