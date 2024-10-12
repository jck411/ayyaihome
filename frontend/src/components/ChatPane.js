// src/components/ChatPane.js

import React from 'react';
import MessageList from './MessageList';

const ChatPane = ({ messages, leftWidth, handleMouseDown, scrollToAIMessage }) => {
  return (
    <div className={`flex flex-grow overflow-hidden transition-all duration-300`}>
      {/* User message pane */}
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

      {/* AI assistant message pane */}
      <div className="flex flex-col message-list" style={{ width: `${100 - leftWidth}%` }}>
        <MessageList
          messages={messages} // AI assistant messages from useMessageLogic
          sender="assistant" // Sender type: assistant
          onMessageClick={null} // No click handler for assistant messages
        />
      </div>
    </div>
  );
};

export default ChatPane;
