// Interface.js
import React from 'react'; // Only import React, no need for useState or useEffect here
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import ModeToggle from './components/ModeToggle';

const Interface = ({
  darkMode,
  toggleDarkMode,
  status,
  messages,
  input,
  setInput,
  sendMessage,
  selectedAPI,
  setSelectedAPI,
  isSidebarOpen,
  toggleSidebar,
  handleMouseDown,
  leftWidth,
  scrollToAIMessage,
}) => {
  return (
    <div className={`min-h-screen w-full flex ${darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'}`}>
      {/* Sidebar */}
      <div className={`fixed top-0 left-0 h-full z-50 transition-transform duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <Sidebar
          isOpen={isSidebarOpen}
          toggleSidebar={toggleSidebar}
          selectedAPI={selectedAPI}
          setSelectedAPI={setSelectedAPI}
          darkMode={darkMode}
        />
      </div>

      {/* Main content */}
      <div className={`flex-grow transition-all duration-300 ${isSidebarOpen ? 'ml-32' : 'ml-0'}`}>
        <div className="max-w-[1200px] mx-auto p-4 flex flex-col h-screen">
          <div className="flex justify-between items-center mb-4">
            <StatusBar status={status} toggleSidebar={toggleSidebar} />
            <ModeToggle darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
          </div>
          <div className="flex flex-grow overflow-hidden">
            <div className="flex" style={{ width: `${leftWidth}%` }}>
              <MessageList
                messages={messages}
                sender="user"
                onMessageClick={scrollToAIMessage}
              />
            </div>
            <div
              className="mid-cursor"
              onMouseDown={handleMouseDown}
            />
            <div className="flex flex-col overflow-hidden" style={{ width: `${100 - leftWidth}%` }}>
              <MessageList messages={messages} sender="assistant" />
            </div>
          </div>
          <MessageInput input={input} setInput={setInput} sendMessage={sendMessage} darkMode={darkMode} />
        </div>
      </div>
    </div>
  );
};

export default Interface;
