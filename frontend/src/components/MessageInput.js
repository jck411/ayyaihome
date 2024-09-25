// Path: frontend/src/components/MessageInput.js

import React, { useRef, useState } from 'react';
import { Send, Mic, MicOff } from 'lucide-react';
import useSpeechToText from '../hooks/useSpeechToText';

const MessageInput = ({ input, setInput, sendMessage, darkMode }) => {
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef(null);

  // Callback when speech is recognized
  const handleResult = (transcript) => {
    if (transcript !== "Speech not recognized.") {
      // Directly send the recognized transcript as a message
      sendMessage(transcript);
      // No need to set the input box
      setInput('');
      textareaRef.current.style.height = 'auto'; // Reset height if necessary
    } else {
      console.log("Speech was not recognized.");
    }
    // Ensure STT is stopped
    setIsListening(false);
  };

  const handleError = (error) => {
    console.error('Speech recognition error:', error);
    setIsListening(false);
  };

  const { startListening, stopListening } = useSpeechToText(
    handleResult,
    handleError,
    () => setIsListening(true),
    () => setIsListening(false)
  );

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(); // Uses the current input state from useMessageLogic
      setInput(''); // Clear input field after sending
      textareaRef.current.style.height = 'auto'; // Reset height after sending
    }
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <div className="bg-inherit p-4">
      <div className="mx-auto" style={{ maxWidth: '600px', width: '100%' }}>
        <form onSubmit={handleSendMessage} className="flex items-start space-x-2">
          {/* Microphone Icon */}
          <button 
            type="button" 
            onClick={toggleListening}
            aria-label={isListening ? "Stop listening" : "Start listening"}
            className="bg-contrast-orange text-white p-2 rounded-l-lg flex-shrink-0"
          >
            {isListening ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
          </button>

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
            className={`flex-grow p-2 border border-contrast-orange focus:border-contrast-orange focus:ring-contrast-orange focus:ring-2 focus:outline-none resize-none ${
              darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'
            }`}
            placeholder="Type your message..."
            rows={1}
          />

          <button
            type="submit"
            className="bg-contrast-orange text-white p-2 rounded-r-lg flex-shrink-0"
          >
            <Send className="w-6 h-6" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default MessageInput;
