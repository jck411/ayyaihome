import React, { useEffect, useRef } from 'react';
import CodeBlock from './CodeBlock';

const renderMessageContent = (content) => {
  const codeBlockRegex = /```(\w+)?\s([\s\S]*?)\s```/g;
  const parts = [];
  let lastIndex = 0;

  content.replace(codeBlockRegex, (match, language, code, offset) => {
    if (lastIndex < offset) {
      parts.push(
        <span key={`text-${lastIndex}`} dangerouslySetInnerHTML={{ __html: content.substring(lastIndex, offset).replace(/\n/g, '<br/>') }} />
      );
    }
    parts.push(<CodeBlock key={offset} code={code.trim()} language={language || 'plaintext'} />);
    lastIndex = offset + match.length;
  });

  if (lastIndex < content.length) {
    parts.push(
      <span key={`text-${lastIndex}`} dangerouslySetInnerHTML={{ __html: content.substring(lastIndex).replace(/\n/g, '<br/>') }} />
    );
  }

  return parts;
};

const MessageList = ({ messages }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex-grow overflow-y-auto mb-4 p-4">
      {messages.map((message) => (
        <div key={message.id} className={`mb-2 ${message.sender === 'user' ? 'text-light-text dark:text-dark-text' : 'text-green-500'}`}>
          <span className="font-bold">{message.sender}: </span>
          {renderMessageContent(message.text)}
          <span className="block text-xs text-gray-500">{message.timestamp}</span>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
