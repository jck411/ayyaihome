module.exports = {
  darkMode: 'class', // Enable dark mode support
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#1D1F21',       // Dark mode background
        'dark-text': '#E5E6E7',     // Dark mode text
        'dark-primary': '#FFAB00',  // Dark mode primary (e.g., status indicator, buttons)

        'light-bg': '#2E3B4E',      // Darker light mode background
        'light-text': '#F5F5F5',    // Darker light mode text
        'light-primary': '#FFAB00', // Light mode primary (e.g., status indicator, buttons)
      },
    },
  },
  plugins: [],
}
