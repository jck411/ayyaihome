import React from 'react';

const Sidebar = ({ isOpen, selectedAPI, setSelectedAPI, darkMode }) => {
  return (
    <div
      className={`fixed left-0 z-40 transition-transform transform ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
      style={{
        top: 'var(--status-bar-height)',
        height: 'calc(100% - var(--status-bar-height))',
        width: '250px',
        backgroundColor: darkMode ? 'var(--dark-bg)' : 'var(--light-bg)',
        color: 'var(--contrast-orange)',
      }}
    >
      <div className="p-4">
        {/* Navigation or menu items */}
        <div className="mt-4">
          <h2 className="font-bold text-contrast-orange">API Selection</h2>
          <div className="mt-2">
            <label className="block cursor-pointer">
              <input
                type="radio"
                name="api-service"
                checked={selectedAPI === 'openai'}
                onChange={() => setSelectedAPI('openai')}
                className="form-radio h-4 w-4 text-contrast-orange mr-2"
                style={{ accentColor: 'var(--contrast-orange)' }}
              />
              OpenAI
            </label>
            <label className="block cursor-pointer">
              <input
                type="radio"
                name="api-service"
                checked={selectedAPI === 'anthropic'}
                onChange={() => setSelectedAPI('anthropic')}
                className="form-radio h-4 w-4 text-contrast-orange mr-2"
                style={{ accentColor: 'var(--contrast-orange)' }}
              />
              Anthropic
            </label>
          </div>
        </div>
        {/* Additional sidebar content */}
        <div className="mt-4">
          <p className="text-contrast-orange">More sidebar content here...</p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
