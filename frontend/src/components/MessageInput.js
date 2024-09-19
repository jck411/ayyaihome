import React, { useRef, useState } from 'react';
import { Send, Mic } from 'lucide-react';
import STTHandler from './STTHandler';

const MessageInput = ({ input, setInput, sendMessage, darkMode, setIsMicActive }) => {
  const textareaRef = useRef(null);
  const [isMicActive, setLocalMicActive] = useState(false);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(e);
      setInput('');
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleTranscription = (transcription, type) => {
    if (type === 'transcribed') {
      setInput(transcription); // Set final transcription into the input field
    }
  };

  const toggleMic = () => {
    const newMicState = !isMicActive;
    setLocalMicActive(newMicState); // Update local mic state
    setIsMicActive(newMicState);    // Update global mic state
  };

  return (
    <div className="bg-inherit p-4">
      <div className="mx-auto" style={{ maxWidth: '600px', width: '100%' }}>
        <form onSubmit={handleSendMessage} className="flex items-start space-x-2">
          <button
            type="button"
            onClick={toggleMic}
            className={`p-2 rounded-lg text-white ${isMicActive ? 'bg-contrast-orange' : 'bg-gray-300'}`}
          >
            <Mic className="w-6 h-6" />
          </button>

          <STTHandler isActive={isMicActive} onTranscription={handleTranscription} />

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
            className={`flex-grow p-2 border border-contrast-orange focus:border-contrast-orange focus:ring-contrast-orange focus:ring-2 focus:outline-none resize-none ${darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'}`}
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
