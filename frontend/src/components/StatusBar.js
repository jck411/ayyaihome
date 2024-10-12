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
  const users = ['Jack', 'Sanja', 'Guest'];

  return (
    <div className="flex items-center justify-between w-full bg-inherit p-4 fixed top-0 left-0 right-0 z-40">
      {/* Left side with Sidebar toggle and User logins */}
      <div className="flex items-center space-x-4">
        {/* Sidebar toggle icon */}
        <div className="cursor-pointer p-2" onClick={toggleSidebar}>
          <FiMenu size={24} style={{ color: 'var(--contrast-orange)' }} />
        </div>

        {/* User login buttons */}
        {users.map((user) => (
          <span
            key={user}
            onClick={() => onLogin(user)}
            className={`cursor-pointer px-2 py-1 ${
              loggedInUser === user ? 'bg-contrast-orange text-white' : 'text-contrast-orange'
            }`}
            style={{ fontWeight: 'bold' }}
          >
            {user}
          </span>
        ))}
      </div>

      {/* Right side with Online status and ModeToggle */}
      <div className="flex items-center space-x-4">
        <span className="text-lg font-bold text-contrast-orange whitespace-nowrap">
          {status === 'connected' ? 'Online' : 'Offline'}
        </span>
        <ModeToggle darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
      </div>
    </div>
  );
};

export default StatusBar;
