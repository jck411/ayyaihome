import React from 'react';
import { Send } from 'lucide-react';

const MessageInput = ({ input, setInput, sendMessage, darkMode }) => {
  return (
    <form onSubmit={sendMessage} className="flex">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className={`flex-grow p-2 rounded-l-lg border border-contrast-orange focus:border-contrast-orange focus:ring-contrast-orange focus:ring-2 focus:outline-none ${darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'}`}
        placeholder="Type your message..."
      />
      <button type="submit" className="bg-contrast-orange text-white p-2 rounded-r-lg">
        <Send className="w-6 h-6" />
      </button>
    </form>
  );
};

export default MessageInput;
