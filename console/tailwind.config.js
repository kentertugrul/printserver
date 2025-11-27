/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ScentCraft brand palette - warm, luxurious feel
        scentcraft: {
          50: '#fdf8f6',
          100: '#f9ede7',
          200: '#f5ddd2',
          300: '#edc4b1',
          400: '#e3a085',
          500: '#d67d5e',
          600: '#c56344',
          700: '#a54f37',
          800: '#874331',
          900: '#6e392b',
          950: '#3b1b14',
        },
        // Dark mode sophisticated palette
        midnight: {
          50: '#f6f6f7',
          100: '#e2e3e5',
          200: '#c4c6cb',
          300: '#9fa2aa',
          400: '#7a7e88',
          500: '#5f636e',
          600: '#4b4e57',
          700: '#3d3f47',
          800: '#34363c',
          900: '#2c2d32',
          950: '#1a1b1f',
        },
      },
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        display: ['Playfair Display', 'serif'],
      },
    },
  },
  plugins: [],
}



