/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1a1a2e',
          light: '#2a2a3e',
          dark: '#0a0a1e',
        },
        secondary: {
          DEFAULT: '#00d4ff',
          light: '#33ddff',
          dark: '#00a8cc',
        },
        accent: {
          DEFAULT: '#7b2cbf',
          light: '#9d4edd',
          dark: '#5a189a',
        },
      },
    },
  },
  plugins: [],
}
