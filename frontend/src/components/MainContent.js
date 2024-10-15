import React from 'react';
import ChatPane from './ChatPane';

const MainContent = ({ appLogic }) => {
  const { messages, leftWidth, handleMouseDown, scrollToAIMessage } = appLogic;

  return (
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
  );
};

export default MainContent;
