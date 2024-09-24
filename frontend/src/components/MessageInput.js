// /home/jack/ayyaihome/frontend/src/components/MessageInput.js

import React, { useEffect } from 'react';
import { Send, Mic, MicOff } from 'lucide-react';
import useSTTService from '../services/sttService';

const MessageInput = ({ input, setInput, sendMessage, darkMode }) => {
  const textareaRef = React.useRef(null);
  const { sttInput, setSTTInput, isSTTOn, startSTT, stopSTT } = useSTTService();

  useEffect(() => {
    if (sttInput !== '') {
      setInput(sttInput);
    }
  }, [sttInput, setInput]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(e); // Trigger sendMessage
      setInput(''); // Clear input field after sending the message
      setSTTInput(''); // Clear STT input
      textareaRef.current.style.height = 'auto'; // Reset height after sending
    }
  };

  const toggleSTT = () => {
    if (isSTTOn) {
      stopSTT();
    } else {
      startSTT();
    }
  };

  return (
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
        className={`flex-grow p-2 rounded-l-lg border border-contrast-orange focus:border-contrast-orange focus:ring-contrast-orange focus:ring-2 focus:outline-none resize-none ${
          darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'
        }`}
        placeholder="Type your message..."
        rows={1}
      />
      <button
        type="button"
        onClick={toggleSTT}
        className={`p-2 flex-shrink-0 rounded-full border ${
          isSTTOn
            ? 'bg-contrast-orange text-white'
            : darkMode
            ? 'bg-dark-bg text-dark-text border-contrast-orange'
            : 'bg-light-bg text-light-text border-contrast-orange'
        }`}
      >
        {isSTTOn ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
      </button>
      <button type="submit" className="bg-contrast-orange text-white p-2 rounded-r-lg flex-shrink-0">
        <Send className="w-6 h-6" />
      </button>
    </form>
  );
};

export default MessageInput;
