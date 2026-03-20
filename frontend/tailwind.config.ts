import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#1E3A8A', // Soares Picon blue
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        ai: {
          suggestion: '#fbbf24', // Yellow for AI suggestions
          confirmed: '#22c55e', // Green for confirmed fields
        },
      },
    },
  },
  plugins: [],
}

export default config
