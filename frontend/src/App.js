import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import { useMessageLogic } from './MessageLogic';

const App = () => {
  const {
    messages,
    input,
    setInput,
    status,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    sendStopSignal,
    setLoggedInUser,
    ttsEnabled,
    setTtsEnabled
  } = useMessageLogic();  // All logic comes from useMessageLogic

  const [darkMode, setDarkMode] = useState(true);
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [leftWidth, setLeftWidth] = useState(30); 
  const [loggedInUser, setLoggedInUserState] = useState(null);

  const onLogin = (user) => {
    setLoggedInUserState(user);
    setLoggedInUser(user);  // Set logged in user from logic
  };

  const toggleDarkMode = () => setDarkMode(!darkMode);
  const toggleSidebar = () => setSidebarOpen(!isSidebarOpen);

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
        sendStopSignal();  // Call stop signal from message logic
        console.log('Sending stop signal via Enter key');
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [sendStopSignal]);

  const handleDrag = (e) => {
    const containerOffset = (window.innerWidth - 950) / 2;
    const newLeftWidth = ((e.clientX - containerOffset) / 950) * 100;
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
    <div className={`min-h-screen w-full`}>
      {/* Sidebar */}
      <div className={`fixed top-0 left-0 h-full z-30 transition-transform duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <Sidebar
          isOpen={isSidebarOpen}
          selectedAPI={selectedAPI}
          setSelectedAPI={setSelectedAPI}
          darkMode={darkMode}
          ttsEnabled={ttsEnabled}
          setTtsEnabled={setTtsEnabled}
        />
      </div>

      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-40">
        <StatusBar 
          status={status} 
          onLogin={onLogin} 
          loggedInUser={loggedInUser} 
          darkMode={darkMode} 
          toggleDarkMode={toggleDarkMode}
          toggleSidebar={toggleSidebar}
        />
      </div>

      {/* Main content area */}
      <div className={`flex flex-col h-screen pt-16 pb-16`}>
        <div className="mx-auto main-content" style={{ maxWidth: '950px', width: '100%' }}>
          {/* Chat area */}
          <div className={`flex flex-grow overflow-hidden transition-all duration-300`}>
            <div className="flex flex-col message-list" style={{ width: `${leftWidth}%` }}>
              <MessageList
                messages={messages}   // Messages from useMessageLogic
                sender="user"
                onMessageClick={scrollToAIMessage}
              />
            </div>
            <div className="mid-cursor-wrapper" onMouseDown={handleMouseDown}>
              <div className="mid-cursor" />
            </div>
            <div className="flex flex-col message-list" style={{ width: `${100 - leftWidth}%` }}>
              <MessageList 
                messages={messages} 
                sender="assistant" 
                onMessageClick={null} 
              />
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="fixed bottom-0 left-0 right-0 z-40">
        <MessageInput 
          input={input} 
          setInput={setInput} 
          sendMessage={sendMessage} 
          darkMode={darkMode} 
        />
      </div>
    </div>
  );
};

export default App;
