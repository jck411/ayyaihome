import React from 'react';
import { Send } from 'lucide-react';

const MessageInput = ({ input, setInput, sendMessage, darkMode }) => {
  return (
    <form onSubmit={sendMessage} className="flex">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className={`flex-grow p-2 rounded-l-lg ${darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'}`}
        placeholder="Type your message..."
      />
      <button type="submit" className="bg-dark-primary dark:bg-light-primary text-white p-2 rounded-r-lg">
        <Send className="w-6 h-6" />
      </button>
    </form>
  );
};

export default MessageInput;
