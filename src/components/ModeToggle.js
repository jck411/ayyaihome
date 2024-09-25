import React from 'react';
import { Sun, Moon } from 'lucide-react';

const ModeToggle = ({ darkMode, toggleDarkMode }) => {
  return (
    <button onClick={toggleDarkMode} className="p-2 rounded-full hover:bg-gray-300 dark:hover:bg-gray-700">
      {darkMode ? <Sun className="w-6 h-6 text-contrast-orange" /> : <Moon className="w-6 h-6 text-contrast-orange" />}
    </button>
  );
};

export default ModeToggle;
