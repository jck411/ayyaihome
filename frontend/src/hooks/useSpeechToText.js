// Path: frontend/src/hooks/useSpeechToText.js

import { useEffect, useRef } from 'react';
import * as SpeechSDK from 'microsoft-cognitiveservices-speech-sdk';

const useSpeechToText = (onResult, onError, onStart, onStop) => {
  const recognizerRef = useRef(null);

  const startListening = () => {
    const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(
      process.env.REACT_APP_SPEECH_KEY,
      process.env.REACT_APP_SPEECH_REGION
    );
    speechConfig.speechRecognitionLanguage = 'en-US';

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

    recognizer.startContinuousRecognitionAsync(() => {
      console.log('Recognition started');
      if (onStart) onStart();
    });
    
    recognizerRef.current = recognizer;
  };

  const stopListening = () => {
    if (recognizerRef.current) {
      recognizerRef.current.stopContinuousRecognitionAsync(() => {
        console.log('Recognition stopped');
        if (onStop) onStop();
      });
      recognizerRef.current = null;
    }
  };

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopListening();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { startListening, stopListening };
};

export default useSpeechToText;
