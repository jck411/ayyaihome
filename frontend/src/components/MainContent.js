// /home/jack/ayyaihome/frontend/src/components/MainContent.js

import React from 'react';
import ChatPane from './ChatPane';

const MainContent = ({ appLogic }) => {
  const { 
    messages, 
    leftWidth, 
    handleMouseDown, 
    scrollToAIMessage,
    sendMessage,
    input,
    setInput,
    status,
    onMessageClick 
  } = appLogic;

  return (
    <div className="flex flex-col h-screen pt-16 pb-16">
      <div className="mx-auto main-content" style={{ maxWidth: '1200px', width: '100%' }}>
        <ChatPane
          messages={messages}
          leftWidth={leftWidth}
          handleMouseDown={handleMouseDown}
          scrollToAIMessage={scrollToAIMessage}
          sendMessage={sendMessage}
          input={input}
          setInput={setInput}
          status={status}
          onMessageClick={onMessageClick}
        />
      </div>
    </div>
  );
};

export default MainContent;
