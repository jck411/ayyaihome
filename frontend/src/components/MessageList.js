import React, { useEffect, useRef } from 'react';
import CodeBlock from './CodeBlock';

const renderMessageContent = (content) => {
  const codeBlockRegex = /```(\w+)?\s([\s\S]*?)\s```/g;
  const parts = [];
  let lastIndex = 0;

  content.replace(codeBlockRegex, (match, language, code, offset) => {
    if (lastIndex < offset) {
      parts.push(
        <p key={`text-${lastIndex}`} style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
          {content.substring(lastIndex, offset)}
        </p>
      );
    }
    parts.push(<CodeBlock key={offset} code={code.trim()} language={language || 'plaintext'} />);
    lastIndex = offset + match.length;
  });

  if (lastIndex < content.length) {
    parts.push(
      <p key={`text-${lastIndex}`} style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
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
    <div className="flex-grow overflow-y-auto p-4 message-list">
      {messages
        .filter((message) => message.sender === sender || (sender === 'user' && message.metadata?.user))
        .map((message) => (
          <div 
            key={message.id} 
            id={`${message.sender === 'assistant' ? `ai-message-${message.id}` : ''}`}
            className={`mb-2 ${message.sender === 'assistant' ? 'ai-response' : 'user-response'}`}
            onClick={message.sender === 'user' && onMessageClick ? () => onMessageClick(message.id + 1) : null}
            style={{ cursor: message.sender === 'user' && onMessageClick ? 'pointer' : 'default' }}
          >
            <span className="font-bold">
              {message.sender === 'assistant'
                ? message.metadata?.assistantType === 'openai'
                  ? 'OpenAI: '
                  : 'Anthropic: '
                : `${message.metadata?.user || 'User'}: `}
            </span>
            <div className="message-text">
              {renderMessageContent(message.text)}
            </div>
            <span className="block text-xs text-gray-500">{message.timestamp}</span>
          </div>
        ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
