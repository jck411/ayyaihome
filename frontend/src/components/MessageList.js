import React, { useEffect, useRef } from 'react';
import CodeBlock from './CodeBlock';

const renderMessageContent = (content) => {
  if (!Array.isArray(content)) {
    return null;
  }

  return content.map((item, index) => {
    if (item.type === 'text') {
      const codeBlockRegex = /```(\w+)?\s([\s\S]*?)\s```/g;
      const parts = [];
      let lastIndex = 0;

      item.text.replace(codeBlockRegex, (match, language, code, offset) => {
        if (lastIndex < offset) {
          parts.push(
            <p key={`text-${lastIndex}`} style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
              {item.text.substring(lastIndex, offset)}
            </p>
          );
        }
        parts.push(<CodeBlock key={offset} code={code.trim()} language={language || 'plaintext'} />);
        lastIndex = offset + match.length;
      });

      if (lastIndex < item.text.length) {
        parts.push(
          <p key={`text-${lastIndex}`} style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
            {item.text.substring(lastIndex)}
          </p>
        );
      }

      return parts;
    }
    return null;
  });
};

const MessageList = ({ messages, role, onMessageClick }) => {
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
        .filter((message) => message.role === role)
        .map((message) => (
          <div 
            key={message.id} 
            id={role === 'assistant' ? `ai-message-msg_${message.id.split('_')[1]}` : `user-message-msg_${message.id.split('_')[1]}`}
            className={`mb-2 ${role === 'assistant' ? 'ai-response' : 'user-response'}`}
            onClick={role === 'user' ? () => onMessageClick(message.id.split('_')[1]) : null}
            style={{ cursor: role === 'user' ? 'pointer' : 'default' }}
          >
            <span className="font-bold">{message.role}: </span>
            {renderMessageContent(message.content)}
            {message.timestamp && (
              <span className="block text-xs text-gray-500">{message.timestamp}</span>
            )}
          </div>
        ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
