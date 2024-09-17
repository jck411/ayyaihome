import React, { useRef } from 'react';
import { Send } from 'lucide-react';

const MessageInput = ({ input, setInput, sendMessage, darkMode }) => {
  const textareaRef = useRef(null);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(e);
      setInput('');
      textareaRef.current.style.height = 'auto';
    }
  };

  return (
    <div className="bg-inherit p-4">
      <div className="mx-auto" style={{ maxWidth: '600px', width: '100%' }}>
        <form onSubmit={handleSendMessage} className="flex items-start space-x-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                handleSendMessage(e);
              }
            }}
            style={{ height: 'auto', maxHeight: '150px', overflowY: 'auto' }}
            className={`flex-grow p-2 rounded-l-lg border border-contrast-orange focus:border-contrast-orange focus:ring-contrast-orange focus:ring-2 focus:outline-none resize-none ${darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'}`}
            placeholder="Type your message..."
            rows={1}
          />
          <button type="submit" className="bg-contrast-orange text-white p-2 rounded-r-lg flex-shrink-0">
            <Send className="w-6 h-6" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default MessageInput;
