module.exports = {
  darkMode: 'class', // Enable dark mode support
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': 'var(--dark-bg)',       // Dark mode background
        'dark-text': 'var(--dark-text)',   // Dark mode text
        'dark-primary': 'var(--contrast-orange)',  // Dark mode primary (new orange)

        'light-bg': 'var(--light-bg)',     // Darker light mode background
        'light-text': 'var(--light-text)', // Darker light mode text
        'light-primary': 'var(--contrast-orange)', // Light mode primary (new orange)

        'contrast-orange': 'var(--contrast-orange)' // Unified contrasting new orange color
      },
    },
  },
  plugins: [],
}
