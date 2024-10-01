///home/jack/ayyaihome/frontend/src/components/MessageInput.js
import React, { useRef, useState } from 'react';
import { Send, Mic, MicOff } from 'lucide-react';
import useSpeechToText from '../hooks/useSpeechToText';

const MessageInput = ({ input, setInput, sendMessage, darkMode }) => {
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef(null);

  // Callback when speech is recognized, updating the input field only
  const handleResult = (transcript) => {
    if (transcript !== "Speech not recognized.") {
      setInput(transcript);  // Update the input box with the recognized speech
    } else {
      console.log("Speech was not recognized.");
    }
  };

  // Handle STT errors
  const handleError = (error) => {
    console.error('Speech recognition error:', error);
    setIsListening(false);
  };

  // Initialize Speech-to-Text hook
  const { startListening, stopListening } = useSpeechToText(
    handleResult,   // Success callback when STT completes
    handleError,    // Error callback
    () => setIsListening(true),  // When STT starts
    () => setIsListening(false)  // When STT stops
  );

  // Handle manual message sending via the input field
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage();  // Uses the current input state from useMessageLogic
      setInput('');  // Clear input field after sending
      textareaRef.current.style.height = 'auto';  // Reset height after sending
    }
  };

  // Toggle the microphone listening state
  const toggleListening = () => {
    if (isListening) {
      stopListening();  // Stop listening if it's already active
    } else {
      startListening();  // Start listening for STT
    }
  };

  return (
    <div className="bg-inherit p-4">
      <div className="mx-auto" style={{ maxWidth: '600px', width: '100%' }}>
        <form onSubmit={handleSendMessage} className="flex items-start space-x-2">
          {/* Microphone Button to Toggle STT */}
          <button 
            type="button" 
            onClick={toggleListening}
            aria-label={isListening ? "Stop listening" : "Start listening"}
            className={`bg-contrast-orange text-white p-2 rounded-l-lg flex-shrink-0 ${
              isListening ? 'pulsating' : ''}`}  // Pulsating effect for "ON" state
          >
            {isListening ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
          </button>

          {/* Textarea Input Field for Manual Message Entry */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}  // Update input on manual typing
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                handleSendMessage(e);  // Send message on Enter key press (without Shift)
              }
            }}
            style={{ height: 'auto', maxHeight: '150px', overflowY: 'auto' }}
            className={`flex-grow p-2 border border-contrast-orange focus:border-contrast-orange focus:ring-contrast-orange focus:ring-2 focus:outline-none resize-none ${
              darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'
            }`}
            placeholder="Type your message..."
            rows={1}
          />

          {/* Send Button */}
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
