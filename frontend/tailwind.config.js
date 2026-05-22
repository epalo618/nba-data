/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#C9A84C',
          dark: '#A8873A',
        },
        surface: {
          DEFAULT: '#1A1D23',
          card: '#21252E',
          hover: '#272B35',
          border: '#2E3340',
        },
      },
    },
  },
  plugins: [],
}
