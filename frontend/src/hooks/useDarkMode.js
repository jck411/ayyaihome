// /home/jack/ayyaihome/frontend/src/hooks/useDarkMode.js

import { useState, useEffect, useCallback } from 'react';

const useDarkMode = () => {
  // State to manage dark mode
  const [darkMode, setDarkMode] = useState(true);

  // Toggle between dark and light mode
  const toggleDarkMode = useCallback(() => setDarkMode(prev => !prev), []);

  // Effect to add or remove the dark mode class from the body element
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]);

  return { darkMode, toggleDarkMode };
};

export default useDarkMode;