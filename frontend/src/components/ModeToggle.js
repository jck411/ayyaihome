import React from 'react';
import { Sun, Moon } from 'lucide-react';

const ModeToggle = ({ darkMode, toggleDarkMode }) => {
  return (
    <button onClick={toggleDarkMode} className="p-2 rounded-full hover:bg-comet-light dark:hover:bg-comet-dark">
      {darkMode ? <Sun className="w-6 h-6 text-comet-orange" /> : <Moon className="w-6 h-6 text-comet-orange" />}
    </button>
  );
};

export default ModeToggle;
