// /home/jack/ayyaihome/frontend/src/components/MessageList.js

import React, { useEffect, useRef } from 'react';
import CodeBlock from './CodeBlock';

const renderMessageContent = (content) => {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)\n```/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    const [fullMatch, language, code] = match;
    const index = match.index;

    if (lastIndex < index) {
      parts.push(
        <p key={`text-${lastIndex}`} style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
          {content.substring(lastIndex, index)}
        </p>
      );
    }

    parts.push(<CodeBlock key={`code-${index}`} code={code.trim()} language={language || 'plaintext'} />);
    lastIndex = index + fullMatch.length;
  }

  if (lastIndex < content.length) {
    parts.push(
      <p key={`text-end-${lastIndex}`} style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
        {content.substring(lastIndex)}
      </p>
    );
  }

  return parts;
};

const MessageList = ({ messages, sender, onMessageClick }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex-grow overflow-y-auto mb-4 p-4 max-h-full">
      {messages
        .filter((message) => message.sender === sender)
        .map((message) => (
          <div 
            key={message.id} 
            id={`${sender === 'assistant' ? `ai-message-${message.id}` : ''}`}
            className={`mb-2 ${sender === 'assistant' ? 'ai-response' : 'user-response'}`}
            onClick={sender === 'user' && onMessageClick ? () => onMessageClick(message.id) : null}
            style={{ cursor: sender === 'user' ? 'pointer' : 'default' }}
          >
            <span className="font-bold" style={{ color: sender === 'assistant' ? 'var(--contrast-orange)' : 'inherit' }}>
              {sender === 'assistant' ? 'Assistant: ' : 'You: '}
            </span>
            {renderMessageContent(message.text)}
            <span className="block text-xs text-gray-500">{message.timestamp}</span>
          </div>
        ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
