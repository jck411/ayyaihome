import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import ModeToggle from './components/ModeToggle';
import { useMessageLogic } from './MessageLogic';

const ChatWebsite = () => {
  const {
    openaiMessages,
    anthropicMessages,
    input,
    setInput,
    status,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    sendStopSignal,
  } = useMessageLogic();

  const [darkMode, setDarkMode] = useState(true);
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [leftWidth, setLeftWidth] = useState(33);

  const messages = selectedAPI === 'openai' ? openaiMessages : anthropicMessages;

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
        sendStopSignal();
        console.log('Sending stop signal via Enter key');
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [sendStopSignal, selectedAPI]);

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

  // This function will scroll to the corresponding assistant message
  const scrollToAIMessage = (userMessageId) => {
    // Convert the user message ID to a number and increment it for the assistant message
    const assistantMessageId = parseInt(userMessageId) + 1;
    
    // Find the assistant message by constructing the corresponding ID
    const element = document.getElementById(`ai-message-msg_${assistantMessageId}`);
  
    if (element) {
      console.log('Attempting to scroll to:', `ai-message-msg_${assistantMessageId}`);
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
      // Retry after a short delay if the element is not found
      setTimeout(() => {
        const retryElement = document.getElementById(`ai-message-msg_${assistantMessageId}`);
        if (retryElement) {
          retryElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
          console.error(`Element not found for id: ${assistantMessageId}`);
        }
      }, 500); // Adjust the delay if necessary
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
                messages={messages || []}
                role="user"
                onMessageClick={scrollToAIMessage}
              />
            </div>
            <div
              className="mid-cursor"
              onMouseDown={handleMouseDown}
            />
            <div className="flex flex-col overflow-hidden" style={{ width: `${100 - leftWidth}%` }}>
              <MessageList messages={messages || []} role="assistant" />
            </div>
          </div>
          <MessageInput input={input} setInput={setInput} sendMessage={sendMessage} darkMode={darkMode} />
        </div>
      </div>
    </div>
  );
};

export default ChatWebsite;
