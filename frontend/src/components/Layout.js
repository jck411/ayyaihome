// /home/jack/ayyaihome/frontend/src/components/Layout.js

import React from 'react';
import Sidebar from './Sidebar';
import StatusBar from './StatusBar';
import MainContent from './MainContent';
import Footer from './Footer';

const Layout = ({ appLogic }) => {
  const {
    isSidebarOpen,
    toggleSidebar,
    selectedAPI,
    setSelectedAPI,
    darkMode,
    toggleDarkMode,
    ttsEnabled,
    setTtsEnabled,
    isConnected,
    isAudioConnected,
    isKeywordConnected,
    onLogin,
    loggedInUser,
    setUserInteracted,
  } = appLogic;

  return (
    <div className="min-h-screen w-full" onClick={() => setUserInteracted(true)}>
      <Sidebar
        isOpen={isSidebarOpen}
        selectedAPI={selectedAPI}
        setSelectedAPI={setSelectedAPI}
        darkMode={darkMode}
        ttsEnabled={ttsEnabled}
        setTtsEnabled={setTtsEnabled}
      />
      <StatusBar
        status={isConnected ? 'connected' : 'disconnected'}
        isAudioConnected={isAudioConnected}
        isKeywordConnected={isKeywordConnected}
        onLogin={onLogin}
        loggedInUser={loggedInUser}
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        toggleSidebar={toggleSidebar}
      />
      <MainContent appLogic={appLogic} />
      <Footer appLogic={appLogic} />
    </div>
  );
};

export default Layout;
