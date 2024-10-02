// src/components/MessageInput.js

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Send, Mic, MicOff } from 'lucide-react';
import useSpeechToText from '../hooks/useSpeechToText';

const MessageInput = ({ input, setInput, sendMessage, darkMode }) => {
  const [sendOnInput, setSendOnInput] = useState(false); // Flag to trigger sending
  const textareaRef = useRef(null);
  const audioRef = useRef(null); // Reference for the audio element

  // Callback when speech is recognized
  const handleResult = useCallback((transcript) => {
    if (transcript !== "Speech not recognized.") {
      setInput(transcript);           // Update the input box with the recognized speech
      setSendOnInput(true);           // Set flag to send the message
      if (audioRef.current) {
        audioRef.current.play();       // Play the sound when speech is recognized
      }
    } else {
      console.log("Speech was not recognized.");
    }
  }, [setInput]);

  // Callback when an error occurs in STT
  const handleError = useCallback((error) => {
    console.error('Speech recognition error:', error);
    // Optionally, you can notify the user about the error here
  }, []);

  // Use the custom hook for Speech-to-Text
  const { isListening, startListening, stopListening } = useSpeechToText(handleResult, handleError);

  // useEffect to send message when sendOnInput is true
  useEffect(() => {
    if (sendOnInput && input.trim()) {
      sendMessage();                     // Send the message using the current input state
      setInput('');                      // Clear input field after sending
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'; // Reset height after sending
      }
      setSendOnInput(false);             // Reset the send flag
    }
  }, [sendOnInput, input, sendMessage, setInput]);

  // Handle manual message sending via the input field
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage();                     // Uses the current input state from useMessageLogic
      setInput('');                      // Clear input field after sending
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'; // Reset height after sending
      }
    }
  };

  // Toggle the microphone listening state
  const toggleListening = () => {
    if (isListening) {
      stopListening();  // Stop listening if it's already active
    } else {
      startListening(); // Start listening for STT
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

      {/* Audio Element for Playing Sound */}
      <audio ref={audioRef} src="/submitsound.mp3" />
    </div>
  );
};

export default MessageInput;
