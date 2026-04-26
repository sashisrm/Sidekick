/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f4ff',
          100: '#e0eaff',
          500: '#4f7ef8',
          600: '#3b6ef0',
          700: '#2a5ce0',
          900: '#1a3a8f',
        },
      },
    },
  },
  plugins: [],
}
