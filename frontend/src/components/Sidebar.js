// /home/jack/ayyaihome/frontend/src/components/Sidebar.js

import React from 'react';
import { FiMenu } from 'react-icons/fi'; // Importing a menu icon from react-icons

const Sidebar = ({ isOpen, toggleSidebar, selectedAPI, setSelectedAPI, darkMode }) => {
  return (
    <>
      {/* Indicator to toggle the sidebar */}
      <div
        className="fixed top-4 left-4 p-2 cursor-pointer z-50"
        style={{ color: 'var(--contrast-orange)' }} // Use contrast orange for the icon
      >
        <FiMenu size={24} onClick={toggleSidebar} />
      </div>

      {/* The sidebar itself */}
      <div
        className={`fixed top-0 left-0 h-full transition-transform duration-300 transform z-40 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{
          width: '250px', // Fixed width for consistency
          backgroundColor: darkMode ? 'var(--dark-bg)' : 'var(--light-bg)', // Apply correct background color
          color: 'var(--contrast-orange)', // Ensure text is also orange
        }}
      >
        <div className="p-6">
          {/* Spacer to align with the toggle icon */}
          <div className="mb-6" style={{ height: '24px' }}></div>

          {/* Service Selection with Radio Buttons */}
          <div className="flex items-center mb-4 cursor-pointer" onClick={() => setSelectedAPI('openai')}>
            <input
              type="radio"
              id="openai"
              name="api-service"
              value="openai"
              checked={selectedAPI === 'openai'}
              onChange={() => setSelectedAPI('openai')}
              className="form-radio h-5 w-5 text-orange-500"
            />
            <label htmlFor="openai" className="ml-3 font-semibold" style={{ color: 'var(--contrast-orange)' }}>
              OpenAI
            </label>
          </div>

          <div className="flex items-center mb-4 cursor-pointer" onClick={() => setSelectedAPI('anthropic')}>
            <input
              type="radio"
              id="anthropic"
              name="api-service"
              value="anthropic"
              checked={selectedAPI === 'anthropic'}
              onChange={() => setSelectedAPI('anthropic')}
              className="form-radio h-5 w-5 text-orange-500"
            />
            <label htmlFor="anthropic" className="ml-3 font-semibold" style={{ color: 'var(--contrast-orange)' }}>
              Anthropic
            </label>
          </div>

          {/* Additional Settings or Links can be added here */}
        </div>
      </div>
    </>
  );
};

export default Sidebar;
