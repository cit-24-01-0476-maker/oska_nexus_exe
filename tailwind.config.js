/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: {
          DEFAULT: '#050B13',
          darker: '#02050A',
          card: '#08101E',
          border: 'rgba(0, 229, 229, 0.15)',
        },
        navy: {
          DEFAULT: '#0B1425',
          light: '#13223E',
          card: 'rgba(11, 20, 37, 0.85)',
        },
        cyan: {
          DEFAULT: '#00E5E5',
          glow: '#00E5E5',
          dim: 'rgba(0, 229, 229, 0.4)',
        },
        violet: {
          DEFAULT: '#8057E9',
          glow: '#8057E9',
          dim: 'rgba(128, 87, 233, 0.4)',
        },
        ice: {
          DEFAULT: '#B9F8FF',
        },
        muted: '#8B9AAF',
      },
      boxShadow: {
        'cyan-glow': '0 0 25px rgba(0, 229, 229, 0.35)',
        'violet-glow': '0 0 25px rgba(128, 87, 233, 0.35)',
        'hologram': '0 0 40px rgba(0, 229, 229, 0.25), inset 0 0 20px rgba(0, 229, 229, 0.1)',
      },
      fontFamily: {
        mono: ['Fira Code', 'JetBrains Mono', 'Consolas', 'monospace'],
        sans: ['Inter', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 12s linear infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        }
      }
    },
  },
  plugins: [],
}
