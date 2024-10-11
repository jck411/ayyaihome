// Refactored App.js with modularized hooks

import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import { useMessageLogic } from './MessageLogic';
import useAudioPlayer from './hooks/useAudioPlayer'; // Import the useAudioPlayer hook
import KeywordListener from './components/KeywordListener'; // Import the KeywordListener component
import useWebSocket from './hooks/useWebSocket'; // Import the WebSocket hook
import useDarkMode from './hooks/useDarkMode'; // Import the useDarkMode hook

const App = () => {
  // Destructure the values from the useMessageLogic hook, which handles most of the app's logic
  const {
    messages,
    input,
    setInput,
    status,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    setLoggedInUser,
    ttsEnabled,
    setTtsEnabled
  } = useMessageLogic();

  // Dark mode management
  const { darkMode, toggleDarkMode } = useDarkMode();

  // State to manage whether the sidebar is open
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  // State to manage the width of the left pane in the chat area
  const [leftWidth, setLeftWidth] = useState(30);
  // State to manage the logged-in user details
  const [loggedInUser, setLoggedInUserState] = useState(null);
  // State to track if user has interacted with the page
  const [userInteracted, setUserInteracted] = useState(false);

  // Initialize the audio player using the custom hook and get control functions
  const { stopCurrentTTS, isTTSPlaying } = useAudioPlayer(userInteracted); // Pass userInteracted state to control audio playback

  // Initialize WebSocket using the custom hook
  const { message, isConnected } = useWebSocket('ws://your-websocket-url');

  // Function to handle user login, updating both local and message logic state
  const onLogin = useCallback((user) => {
    setLoggedInUserState(user);
    setLoggedInUser(user);  // Set logged in user from logic
  }, [setLoggedInUser]);

  // Toggle the sidebar's visibility
  const toggleSidebar = useCallback(() => setSidebarOpen(prev => !prev), []);

  // Effect to handle the Shift key press to stop TTS
  const handleKeyDown = useCallback((event) => {
    if (event.key === "Shift") {
      if (isTTSPlaying) {
        stopCurrentTTS();  // Stop TTS when Shift key is pressed
        console.log('Stopping TTS via Shift key');
      }
    }
  }, [stopCurrentTTS, isTTSPlaying]);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);

    // Cleanup the event listener when the component unmounts
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);

  // Effect to listen for any user interaction to allow audio playback
  useEffect(() => {
    const handleUserInteraction = () => {
      setUserInteracted(true);
      window.removeEventListener('click', handleUserInteraction);
      window.removeEventListener('keydown', handleUserInteraction);
    };

    // Add event listeners for user interaction
    window.addEventListener('click', handleUserInteraction);
    window.addEventListener('keydown', handleUserInteraction);

    // Cleanup the event listeners
    return () => {
      window.removeEventListener('click', handleUserInteraction);
      window.removeEventListener('keydown', handleUserInteraction);
    };
  }, []);

  // Function to handle dragging the middle cursor to resize the message list panes
  const handleDrag = useCallback((e) => {
    // Calculate the offset for the draggable container
    const containerOffset = (window.innerWidth - 950) / 2;
    // Calculate new width as a percentage of the container's width
    const newLeftWidth = ((e.clientX - containerOffset) / 950) * 100;
    // Set new width if within acceptable bounds (20% to 80%)
    if (newLeftWidth > 20 && newLeftWidth < 80) {
      setLeftWidth(newLeftWidth);
    }
  }, []);

  // Function to handle the end of dragging
  const handleDragEnd = useCallback(() => {
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', handleDragEnd);
  }, [handleDrag]);

  // Function to start the dragging process
  const handleMouseDown = useCallback(() => {
    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', handleDragEnd);
  }, [handleDrag, handleDragEnd]);

  // Function to scroll to a specific AI message by ID
  const scrollToAIMessage = useCallback((id) => {
    const element = document.getElementById(`ai-message-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, []);

  // Function to handle sending a message without stopping TTS
  const handleSendMessage = useCallback(() => {
    sendMessage(); 
  }, [sendMessage]);

  return (
    <div className={`min-h-screen w-full`} onClick={() => setUserInteracted(true)}> {/* Mark user interaction */}
      {/* Sidebar */}
      <div className={`fixed top-0 left-0 h-full z-30 transition-transform duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <Sidebar
          isOpen={isSidebarOpen} // Sidebar visibility state
          selectedAPI={selectedAPI} // API selection state
          setSelectedAPI={setSelectedAPI} // Function to set selected API
          darkMode={darkMode} // Dark mode state
          ttsEnabled={ttsEnabled} // Text-to-Speech enabled state
          setTtsEnabled={setTtsEnabled} // Function to enable/disable TTS
        />
      </div>

      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-40">
        <StatusBar
          status={status} // Current status from message logic
          onLogin={onLogin} // Login handler
          loggedInUser={loggedInUser} // Currently logged-in user
          darkMode={darkMode} // Dark mode state
          toggleDarkMode={toggleDarkMode} // Function to toggle dark mode
          toggleSidebar={toggleSidebar} // Function to toggle sidebar
        />
      </div>

      {/* Main content area */}
      <div className={`flex flex-col h-screen pt-16 pb-16`}>
        <div className="mx-auto main-content" style={{ maxWidth: '950px', width: '100%' }}>
          {/* Chat area */}
          <div className={`flex flex-grow overflow-hidden transition-all duration-300`}>
            <div className="flex flex-col message-list" style={{ width: `${leftWidth}%` }}>
              <MessageList
                messages={messages} // User messages from useMessageLogic
                sender="user" // Sender type: user
                onMessageClick={scrollToAIMessage} // Scroll handler for messages
              />
            </div>
            {/* Divider for resizing the panes */}
            <div className="mid-cursor-wrapper" onMouseDown={handleMouseDown}>
              <div className="mid-cursor" />
            </div>
            <div className="flex flex-col message-list" style={{ width: `${100 - leftWidth}%` }}>
              <MessageList
                messages={messages} // AI assistant messages from useMessageLogic
                sender="assistant" // Sender type: assistant
                onMessageClick={null} // No click handler for assistant messages
              />
            </div>
          </div>
        </div>
      </div>

      {/* Keyword Listener */}
      <KeywordListener />  {/* Added KeywordListener component */}

      {/* Footer */}
      <div className="fixed bottom-0 left-0 right-0 z-40">
        <MessageInput
          input={input} // Current message input state
          setInput={setInput} // Function to set input value
          sendMessage={handleSendMessage} // Send message without stopping TTS
          darkMode={darkMode} // Dark mode state
          stopCurrentTTS={stopCurrentTTS} // Added stopCurrentTTS prop
        />
      </div>

      {/* Stop TTS Button */}
      <div className="fixed bottom-20 right-4 z-50">
        <button
          onClick={stopCurrentTTS}
          className={`${
            isTTSPlaying ? 'bg-red-500 hover:bg-red-600' : 'bg-gray-400 cursor-not-allowed'
          } text-white p-3`}
          aria-label="Stop TTS"
          title="Stop TTS"
          disabled={!isTTSPlaying}
        >
          {/* "X" Icon */}
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none"
               viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </div>
  );
};

export default App;