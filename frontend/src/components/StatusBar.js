import React from 'react';
import ModeToggle from './ModeToggle';
import { FiMenu } from 'react-icons/fi';

const StatusBar = ({
  status,
  onLogin,
  loggedInUser,
  darkMode,
  toggleDarkMode,
  toggleSidebar
}) => {
  return (
    <div className="flex items-center justify-between w-full space-x-4 overflow-x-auto bg-inherit p-4">
      {/* Left side with Sidebar toggle and User logins */}
      <div className="flex items-center space-x-4">
        {/* Sidebar toggle icon */}
        <div className="cursor-pointer p-2" onClick={toggleSidebar}>
          <FiMenu size={24} style={{ color: 'var(--contrast-orange)' }} />
        </div>

        {/* User login buttons */}
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
      <div className="flex items-center space-x-4">
        <span className="text-lg font-bold text-contrast-orange whitespace-nowrap">Online</span>
        <ModeToggle darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
      </div>
    </div>
  );
};

export default StatusBar;
