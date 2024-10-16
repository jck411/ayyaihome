// src/components/MessageInput.js

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Send, Mic, MicOff } from 'lucide-react';
import { useSelector, useDispatch } from 'react-redux';
import useSpeechToText from '../hooks/useSpeechToText';
import { resetKeyword } from '../slices/keywordSlice';
import { setIsListening } from '../slices/micSlice';

const MessageInput = ({ input, setInput, sendMessage, darkMode, stopCurrentTTS }) => {
  const dispatch = useDispatch();
  const currentKeyword = useSelector((state) => state.keyword.currentKeyword);
  const isListening = useSelector((state) => state.mic.isListening);
  const isTTSPlaying = useSelector((state) => state.mic.isTTSPlaying);
  const lastActivityTime = useSelector((state) => state.mic.lastActivityTime);

  const [sendOnInput, setSendOnInput] = useState(false);
  const textareaRef = useRef(null);
  const audioRef = useRef(null);
  const inactivityTimerRef = useRef(null);

  // Callback when speech is recognized
  const handleResult = useCallback(
    (transcript) => {
      if (transcript !== 'Speech not recognized.') {
        stopCurrentTTS(); // Stop any ongoing TTS
        setInput(transcript); // Update the input box with the recognized speech
        setSendOnInput(true); // Set flag to send the message
        if (audioRef.current) {
          audioRef.current.play().catch((error) => {
            console.error('Failed to play submit sound:', error);
          }); // Play the sound when speech is recognized
        }
      } else {
        console.log('Speech was not recognized.'); // Log if the speech was not recognized
      }
    },
    [stopCurrentTTS, setInput]
  );

  // Callback when an error occurs in Speech-to-Text (STT)
  const handleError = useCallback((error) => {
    console.error('Speech recognition error:', error); // Log the error
    // Optionally, you can notify the user about the error here
  }, []);

  // Use the custom hook for Speech-to-Text functionality
  const { startListening, stopListening } = useSpeechToText(handleResult, handleError);

  // Effect to send message automatically when sendOnInput flag is true
  useEffect(() => {
    if (sendOnInput && input.trim()) {
      sendMessage(); // Send the message using the current input state
      setInput(''); // Clear input field after sending
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'; // Reset height after sending
      }
      setSendOnInput(false); // Reset the send flag
    }
  }, [sendOnInput, input, sendMessage, setInput]);

  // Handle manual message sending via the input field
  const handleSendMessage = useCallback(
    (e) => {
      e.preventDefault(); // Prevent the default form submission behavior
      if (input.trim()) {
        sendMessage(); // Send the message using the current input state
        setInput(''); // Clear input field after sending
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto'; // Reset height after sending
        }
      }
    },
    [input, sendMessage, setInput]
  );

  // Toggle the microphone listening state
  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening(); // Stop listening if it's already active
      dispatch(setIsListening(false)); // Update Redux state
    } else {
      startListening(); // Start listening for speech-to-text
      dispatch(setIsListening(true)); // Update Redux state
    }
  }, [isListening, startListening, stopListening, dispatch]);

  // Effect to respond to keyword detections
  useEffect(() => {
    if (currentKeyword) {
      console.log(`Keyword detected: ${currentKeyword}`);
      startListening(); // Start listening when a keyword is detected
      dispatch(setIsListening(true)); // Update Redux state
      // Optionally, provide user feedback or handle specific keywords differently
      dispatch(resetKeyword()); // Reset keyword after handling
    }
  }, [currentKeyword, startListening, dispatch]);

  // Monitor inactivity
  useEffect(() => {
    // Clear existing timer
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
    }

    // Set new timer if mic is listening
    if (isListening) {
      inactivityTimerRef.current = setTimeout(() => {
        // Check if TTS is not playing
        if (!isTTSPlaying) {
          console.log('Inactivity detected. Stopping microphone.');
          stopListening(); // Stop the mic
          dispatch(setIsListening(false)); // Update Redux state
        }
      }, 5000); // 5 seconds
    }

    // Cleanup function
    return () => {
      if (inactivityTimerRef.current) {
        clearTimeout(inactivityTimerRef.current);
      }
    };
  }, [lastActivityTime, isListening, isTTSPlaying, stopListening, dispatch]);

  return (
    <div className="bg-inherit p-4">
      <div className="mx-auto" style={{ maxWidth: '600px', width: '100%' }}>
        <form onSubmit={handleSendMessage} className="flex items-start space-x-2">
          {/* Microphone Button to Toggle STT */}
          <button
            type="button"
            onClick={toggleListening} // Toggle listening state when button is clicked
            aria-label={isListening ? 'Stop listening' : 'Start listening'} // Update aria-label based on listening state
            className={`bg-contrast-orange text-white p-2 rounded-l-lg flex-shrink-0 ${
              isListening ? 'pulsating' : ''
            }`} // Apply pulsating effect if listening
          >
            {isListening ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
            {/* Change icon based on listening state */}
          </button>

          {/* Textarea Input Field for Manual Message Entry */}
          <textarea
            ref={textareaRef} // Reference for the textarea element
            value={input} // Controlled component value
            onChange={(e) => setInput(e.target.value)} // Update input state on manual typing
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                handleSendMessage(e); // Send message on Enter key press (without Shift)
              }
            }}
            style={{ height: 'auto', maxHeight: '150px', overflowY: 'auto' }} // Set textarea height and limit max height
            className={`flex-grow p-2 border border-contrast-orange focus:border-contrast-orange focus:ring-contrast-orange focus:ring-2 focus:outline-none resize-none ${
              darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text' // Apply styles based on dark mode
            }`}
            placeholder="Type your message..." // Placeholder text for the input field
            rows={1} // Set initial number of rows to 1
          />

          {/* Send Button */}
          <button
            type="submit" // Submit button to send the message
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
