/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: '#00B7F3',
        dark: '#131720',
        'dark-lighter': '#1a2332',
      },
    },
  },
  plugins: [],
}