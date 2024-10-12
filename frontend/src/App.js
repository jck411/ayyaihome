import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import ChatPane from './components/ChatPane';
import MessageInput from './components/MessageInput';
import StopTTSButton from './components/StopTTSButton';
import KeywordListener from './components/KeywordListener';
import { useAppLogic } from './hooks/useAppLogic';

const App = () => {
  const {
    messages,
    input,
    setInput,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    loggedInUser,
    onLogin,
    darkMode,
    toggleDarkMode,
    isSidebarOpen,
    toggleSidebar,
    stopCurrentTTS,  // Make sure stopCurrentTTS is destructured here
    isTTSPlaying,
    isConnected,
    leftWidth,
    handleMouseDown,
    scrollToAIMessage,
    setUserInteracted,
  } = useAppLogic();

  // TTS toggle state
  const [ttsEnabled, setTtsEnabled] = useState(false); // This manages TTS toggle

  return (
    <div className="min-h-screen w-full" onClick={() => setUserInteracted(true)}>
      <Sidebar
        isOpen={isSidebarOpen}
        selectedAPI={selectedAPI}
        setSelectedAPI={setSelectedAPI}
        darkMode={darkMode}
        ttsEnabled={ttsEnabled}   // Pass ttsEnabled state
        setTtsEnabled={setTtsEnabled}  // Pass setTtsEnabled to Sidebar
      />

      <StatusBar
        status={isConnected ? 'connected' : 'disconnected'}
        onLogin={onLogin}
        loggedInUser={loggedInUser}
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        toggleSidebar={toggleSidebar}
      />

      <div className="flex flex-col h-screen pt-16 pb-16">
        <div className="mx-auto main-content" style={{ maxWidth: '950px', width: '100%' }}>
          <ChatPane
            messages={messages}
            leftWidth={leftWidth}
            handleMouseDown={handleMouseDown}
            scrollToAIMessage={scrollToAIMessage}
          />
        </div>
      </div>

      <KeywordListener />

      <div className="fixed bottom-0 left-0 right-0 z-40 p-4">
        <div className="mx-auto" style={{ maxWidth: '600px', width: '100%' }}>
          <MessageInput
            input={input}
            setInput={setInput}
            sendMessage={sendMessage}
            darkMode={darkMode}
            stopCurrentTTS={stopCurrentTTS}  // Pass stopCurrentTTS here
          />
        </div>
        <div className="fixed bottom-20 right-4 z-50">
          <StopTTSButton isTTSPlaying={isTTSPlaying} stopCurrentTTS={stopCurrentTTS} />
        </div>
      </div>
    </div>
  );
};

export default App;
