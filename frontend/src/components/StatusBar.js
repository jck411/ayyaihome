import React from 'react';

const StatusBar = ({ status }) => {
  return (
    <div className="flex items-center justify-end mb-4 relative z-10">
      <span className="text-lg font-bold text-contrast-orange mr-2 ml-10">{status}</span> {/* Add left margin to move status away from the sidebar icon */}
    </div>
  );
};

export default StatusBar;
