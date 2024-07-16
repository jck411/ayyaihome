import React from 'react';

const StatusBar = ({ status }) => {
  return (
    <div className="flex items-center justify-end mb-4">
      <span className="text-sm text-dark-primary dark:text-light-primary">{status}</span>
    </div>
  );
};

export default StatusBar;
