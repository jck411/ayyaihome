import React from 'react';
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import { useMessageLogic } from './MessageLogic';
import useAudioPlayer from './hooks/useAudioPlayer';
import KeywordListener from './components/KeywordListener';
import useWebSocket from './hooks/useWebSocket';
import useDarkMode from './hooks/useDarkMode';
import useMessagePaneResizer from './hooks/useMessagePaneResizer';
import useSidebarState from './hooks/useSidebarState';
import useUserInteractionTracker from './hooks/useUserInteractionTracker';
import useShiftKeyHandler from './hooks/useShiftKeyHandler';
import useScrollToMessage from './hooks/useScrollToMessage';

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
    loggedInUser,
    onLogin,
    ttsEnabled,
    setTtsEnabled
  } = useMessageLogic();

  // Dark mode management
  const { darkMode, toggleDarkMode } = useDarkMode();

  // Sidebar state management
  const { isSidebarOpen, toggleSidebar } = useSidebarState();

  // User interaction tracking
  const { userInteracted, setUserInteracted } = useUserInteractionTracker();

  // Initialize the audio player using the custom hook and get control functions
  const { stopCurrentTTS, isTTSPlaying } = useAudioPlayer(userInteracted);

  // Initialize WebSocket using the custom hook
  const { message, isConnected } = useWebSocket('ws://your-websocket-url');

  // Pane resizing logic now managed by useMessagePaneResizer
  const { leftWidth, handleMouseDown } = useMessagePaneResizer();

  // Shift key handler for stopping TTS
  useShiftKeyHandler(stopCurrentTTS, isTTSPlaying);

  // Scroll to message logic
  const { scrollToAIMessage } = useScrollToMessage();

  // Function to handle sending a message without stopping TTS
  const handleSendMessage = () => {
    sendMessage();
  };

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
          onLogin={onLogin} // Login handler from message logic
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
