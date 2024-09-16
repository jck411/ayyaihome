import React from 'react';
import ModeToggle from './ModeToggle';

const StatusBar = ({ status, onLogin, loggedInUser, darkMode, toggleDarkMode }) => {
  return (
    <div className="flex items-center justify-between mb-4 relative z-10 w-full">
      {/* Left side with user buttons */}
      <div className="flex items-center space-x-4">
        {/* Display the names with background only when the user is logged in */}
        <span
          onClick={() => onLogin('Jack')}
          className={`cursor-pointer px-2 py-1 ${
            loggedInUser === 'Jack' ? 'bg-contrast-orange text-white' : 'text-contrast-orange'
          }`}
          style={{ fontWeight: 'bold' }}
        >
          Jack
        </span>

        <span
          onClick={() => onLogin('Sanja')}
          className={`cursor-pointer px-2 py-1 ${
            loggedInUser === 'Sanja' ? 'bg-contrast-orange text-white' : 'text-contrast-orange'
          }`}
          style={{ fontWeight: 'bold' }}
        >
          Sanja
        </span>

        <span
          onClick={() => onLogin('Guest')}
          className={`cursor-pointer px-2 py-1 ${
            loggedInUser === 'Guest' ? 'bg-contrast-orange text-white' : 'text-contrast-orange'
          }`}
          style={{ fontWeight: 'bold' }}
        >
          Guest
        </span>
      </div>

      {/* Right side with Online status and ModeToggle */}
      <div className="flex items-center space-x-4 ml-auto">
        {/* Online status */}
        <span className="text-lg font-bold text-contrast-orange">Online</span>

        {/* ModeToggle component for dark mode */}
        <ModeToggle darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
      </div>
    </div>
  );
};

export default StatusBar;
