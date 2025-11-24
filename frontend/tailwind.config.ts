import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#00E5FF',
          50: '#E6FDFF',
          100: '#C0FAFF',
          200: '#8AF6FF',
          300: '#52F1FF',
          400: '#1EEBFF',
          500: '#00E5FF',
          600: '#00B7CC',
          700: '#008899',
          800: '#005A66',
          900: '#002C33',
        },
      },
      boxShadow: {
        glow: '0 0 20px rgba(0, 229, 255, 0.6)',
      },
      backgroundImage: {
        grid: 'radial-gradient(rgba(0,229,255,0.2) 1px, transparent 1px)',
      },
      backgroundSize: {
        grid: '24px 24px',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-in': 'slide-in 0.3s ease-out',
      },
    },
  },
  plugins: [],
}

export default config



