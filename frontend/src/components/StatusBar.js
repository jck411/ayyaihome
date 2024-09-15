import React from 'react';

const StatusBar = ({ status, onLogin, loggedInUser }) => {
  return (
    <div className="flex items-center justify-end mb-4 relative z-10 space-x-4">
      <span className="text-lg font-bold text-contrast-orange mr-4">Online</span>

      {/* Display the names with background only when the user is logged in */}
      <span
        onClick={() => onLogin('Jack')}
        className={`cursor-pointer px-2 py-1 ${
          loggedInUser === 'Jack' ? 'bg-contrast-orange text-white' : 'text-contrast-orange'
        }`}
        style={{ fontWeight: 'bold' }}  // Keeps font size and weight consistent
      >
        Jack
      </span>

      <span
        onClick={() => onLogin('Sanja')}
        className={`cursor-pointer px-2 py-1 ${
          loggedInUser === 'Sanja' ? 'bg-contrast-orange text-white' : 'text-contrast-orange'
        }`}
        style={{ fontWeight: 'bold' }}  // Keeps font size and weight consistent
      >
        Sanja
      </span>
    </div>
  );
};

export default StatusBar;
