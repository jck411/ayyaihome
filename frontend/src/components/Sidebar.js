import React from 'react';
import { FiMenu } from 'react-icons/fi'; // Importing a menu icon from react-icons

const Sidebar = ({ isOpen, toggleSidebar, selectedAPI, setSelectedAPI, darkMode }) => {
  return (
    <>
      {/* Indicator to toggle the sidebar */}
      <div
        className="fixed top-0 left-0 p-2 cursor-pointer z-50"
        style={{ margin: '8px', color: 'var(--contrast-orange)' }}  // Use contrast orange for the icon
      >
        <FiMenu size={24} onClick={toggleSidebar} />
      </div>

      {/* The sidebar itself */}
      <div
        className={`fixed top-0 left-0 h-full transition-transform transform w-64 z-40 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
        style={{
          backgroundColor: darkMode ? 'var(--dark-bg)' : 'var(--light-bg)',  // Apply correct background color
          color: 'var(--contrast-orange)',  // Ensure text is also orange
        }}
      >
        <div className="p-4">
          {/* Spacer to maintain the same layout */}
          <div className="mb-4" style={{ height: '24px' }}></div>
          
          {/* Service Selection with Radio Buttons (Right-aligned next to text) */}
          <div className="flex items-center mb-2 cursor-pointer" onClick={() => setSelectedAPI('openai')}>
            <label className="font-bold mr-2" style={{ color: 'var(--contrast-orange)' }}>
              OpenAI
            </label>
            <input
              type="radio"
              name="api-service"
              checked={selectedAPI === 'openai'}
              onChange={() => setSelectedAPI('openai')}
              className="form-radio h-4 w-4 text-contrast-orange"
              style={{ accentColor: 'var(--contrast-orange)' }} // Radio button filled with orange
            />
          </div>

          <div className="flex items-center mb-2 cursor-pointer" onClick={() => setSelectedAPI('anthropic')}>
            <label className="font-bold mr-2" style={{ color: 'var(--contrast-orange)' }}>
              Anthropic
            </label>
            <input
              type="radio"
              name="api-service"
              checked={selectedAPI === 'anthropic'}
              onChange={() => setSelectedAPI('anthropic')}
              className="form-radio h-4 w-4 text-contrast-orange"
              style={{ accentColor: 'var(--contrast-orange)' }} // Radio button filled with orange
            />
          </div>

        </div>
      </div>
    </>
  );
};

export default Sidebar;
