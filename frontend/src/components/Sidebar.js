import React from 'react';
import { FiMenu } from 'react-icons/fi'; // Importing a menu icon from react-icons

const Sidebar = ({ isOpen, toggleSidebar, selectedAPI, setSelectedAPI }) => {
  return (
    <>
      {/* Indicator to toggle the sidebar */}
      <div className="fixed top-1/2 left-0 transform -translate-y-1/2 p-2 bg-gray-800 text-white cursor-pointer z-50">
        <FiMenu size={24} onClick={toggleSidebar} />
      </div>

      {/* The sidebar itself */}
      <div
        className={`fixed top-0 left-0 h-full bg-gray-800 text-white transition-transform transform ${isOpen ? 'translate-x-0' : '-translate-x-full'} w-64 z-40`}
      >
        <div className="p-4">
          <h2 className="text-xl font-semibold mb-4">Select Service</h2>
          <button
            className={`block w-full text-left py-2 px-4 rounded ${selectedAPI === 'openai' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}
            onClick={() => setSelectedAPI('openai')}
          >
            OpenAI
          </button>
          <button
            className={`block w-full text-left py-2 px-4 rounded mt-2 ${selectedAPI === 'anthropic' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}
            onClick={() => setSelectedAPI('anthropic')}
          >
            Anthropic
          </button>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
