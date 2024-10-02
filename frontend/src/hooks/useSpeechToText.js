// src/hooks/useSpeechToText.js

import { useEffect, useRef, useState, useCallback } from 'react';
import * as SpeechSDK from 'microsoft-cognitiveservices-speech-sdk';

/**
 * Custom Hook for Speech-to-Text functionality using Microsoft Cognitive Services.
 *
 * @param {function} onResult - Callback function to handle recognized speech.
 * @param {function} onError - Callback function to handle errors.
 * @param {string} language - Language for speech recognition (default: 'en-US').
 * @returns {object} - Contains isListening state, startListening, and stopListening functions.
 */
const useSpeechToText = (onResult, onError, language = 'en-US') => {
  const [isListening, setIsListening] = useState(false);
  const recognizerRef = useRef(null);

  // Define stopListening first
  const stopListening = useCallback(() => {
    if (recognizerRef.current) {
      recognizerRef.current.stopContinuousRecognitionAsync(
        () => {
          console.log('Recognition stopped');
          setIsListening(false);
        },
        (err) => {
          console.error('Failed to stop recognition:', err);
          onError(err);
        }
      );
      recognizerRef.current = null;
    }
  }, [onError]);

  // Now define startListening and include stopListening in dependencies
  const startListening = useCallback(() => {
    if (isListening) return; // Prevent multiple recognizers

    const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(
      process.env.REACT_APP_SPEECH_KEY,
      process.env.REACT_APP_SPEECH_REGION
    );
    speechConfig.speechRecognitionLanguage = language;

    const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
    const recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

    recognizer.recognizing = (s, e) => {
      console.log(`Recognizing: ${e.result.text}`);
    };

    recognizer.recognized = (s, e) => {
      if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
        onResult(e.result.text);
      } else {
        onResult("Speech not recognized.");
      }
    };

    recognizer.canceled = (s, e) => {
      console.error(`Canceled: ${e.errorDetails}`);
      onError(e.errorDetails);
      stopListening();
    };

    recognizer.sessionStopped = () => {
      console.log('Session stopped');
      stopListening();
    };

    recognizer.startContinuousRecognitionAsync(
      () => {
        console.log('Recognition started');
        setIsListening(true);
      },
      (err) => {
        console.error('Failed to start recognition:', err);
        onError(err);
      }
    );

    recognizerRef.current = recognizer;
  }, [isListening, language, onResult, onError, stopListening]); // Added 'stopListening'

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopListening();
    };
  }, [stopListening]);

  return { isListening, startListening, stopListening };
};

export default useSpeechToText;
