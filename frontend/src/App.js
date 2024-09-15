import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import ModeToggle from './components/ModeToggle';
import { useMessageLogic } from './MessageLogic';  // Import message logic

const ChatWebsite = () => {
  const {
    messages,
    input,
    setInput,
    status,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    sendStopSignal,  // Ensure sendStopSignal is destructured here
  } = useMessageLogic();  // Use the custom hook for messaging logic

  const [darkMode, setDarkMode] = useState(true);
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [leftWidth, setLeftWidth] = useState(33);

  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Enter" && event.target.tagName !== "TEXTAREA") {
        event.preventDefault();
        sendStopSignal();  // Call sendStopSignal when Enter is pressed
        console.log('Sending stop signal via Enter key');
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [sendStopSignal, selectedAPI]);  // Ensure dependencies are updated

  const toggleDarkMode = () => setDarkMode(!darkMode);
  const toggleSidebar = () => setSidebarOpen(!isSidebarOpen);

  const handleDrag = (e) => {
    const newLeftWidth = (e.clientX / window.innerWidth) * 100;
    if (newLeftWidth > 20 && newLeftWidth < 80) {
      setLeftWidth(newLeftWidth);
    }
  };

  const handleDragEnd = () => {
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', handleDragEnd);
  };

  const handleMouseDown = () => {
    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', handleDragEnd);
  };

  const scrollToAIMessage = (id) => {
    const element = document.getElementById(`ai-message-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div className={`min-h-screen w-full flex ${darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'}`}>
      <div className={`fixed top-0 left-0 h-full z-50 transition-transform duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <Sidebar
          isOpen={isSidebarOpen}
          toggleSidebar={toggleSidebar}
          selectedAPI={selectedAPI}
          setSelectedAPI={setSelectedAPI}
          darkMode={darkMode}
        />
      </div>

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
              <MessageList 
                messages={messages} 
                sender="assistant" 
                onMessageClick={null}  // Remove click handler for assistants
              />
            </div>
          </div>
          <MessageInput input={input} setInput={setInput} sendMessage={sendMessage} darkMode={darkMode} />
        </div>
      </div>
    </div>
  );
};

export default ChatWebsite;
