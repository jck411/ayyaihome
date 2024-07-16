import React from 'react';

const StatusBar = ({ status }) => {
  return (
    <div className="flex items-center justify-end mb-4">
      <span className="text-lg font-bold text-contrast-orange">{status}</span>
    </div>
  );
};

export default StatusBar;
