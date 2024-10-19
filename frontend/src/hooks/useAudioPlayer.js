// src/hooks/useAudioPlayer.js

import { useEffect, useRef, useCallback, useState } from 'react';
import { useDispatch } from 'react-redux';
import { setIsTTSPlaying as setIsTTSPlayingAction, updateLastActivityTime } from '../slices/micSlice';

const SUPPORTED_FORMATS = [
  'audio/mpeg',                    // MP3
  'audio/aac',                     // AAC
  'audio/ogg; codecs=opus',        // OPUS in OGG container
  'audio/webm; codecs=opus'        // OPUS in WebM container
];

const useAudioPlayer = (userInteracted) => {
  const dispatch = useDispatch();
  const currentAudioRef = useRef(null);
  const isFirstMessage = useRef(true);
  const audioFormat = useRef('audio/mpeg'); // Default format
  const audioQueue = useRef([]); // Queue to hold incoming audio data
  const isPlayingRef = useRef(false); // Flag to indicate if audio is playing
  const wsRef = useRef(null); // Reference to WebSocket
  const [isTTSPlaying, setIsTTSPlaying] = useState(false); // State to track TTS status
  const isIntentionalStopRef = useRef(false); // Flag to indicate intentional stop
  const [isConnected, setIsConnected] = useState(false); // State to track WebSocket connection status

  // Function to stop current TTS playback without closing the WebSocket
  const stopCurrentTTS = useCallback(() => {
    isIntentionalStopRef.current = true; // Indicate that the stop is intentional

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.src = '';
      currentAudioRef.current = null;
      console.log('Current audio playback stopped.');
    }
    audioQueue.current = []; // Clear any pending audio chunks
    isPlayingRef.current = false;
    setIsTTSPlaying(false);
    dispatch(setIsTTSPlayingAction(false)); // Update Redux state

    // Reset the intentional stop flag after a short delay to ensure the error event is captured
    setTimeout(() => {
      isIntentionalStopRef.current = false;
    }, 100);
  }, [dispatch]);

  useEffect(() => {
    if (!userInteracted) {
      return; // Do not initialize WebSocket until user has interacted
    }

    let ws;

    const playNext = () => {
      if (audioQueue.current.length === 0 || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        isPlayingRef.current = false;
        setIsTTSPlaying(false);
        dispatch(setIsTTSPlayingAction(false)); // Update Redux state
        return;
      }

      const audioData = audioQueue.current.shift();
      const blob = new Blob([audioData], { type: audioFormat.current });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);

      currentAudioRef.current = audio;
      setIsTTSPlaying(true);
      dispatch(setIsTTSPlayingAction(true)); // Update Redux state
      dispatch(updateLastActivityTime()); // Update activity time

      // Handle the end of the audio playback
      audio.onended = () => {
        URL.revokeObjectURL(url);
        setIsTTSPlaying(false);
        dispatch(setIsTTSPlayingAction(false)); // Update Redux state
        playNext();
      };

      // Handle audio playback errors
      audio.onerror = (e) => {
        if (isIntentionalStopRef.current) {
          // Suppress errors caused by intentional stops
          console.log('Intentional stop detected. Suppressing audio playback error.');
        } else {
          console.error('Audio playback error:', e);
        }
        URL.revokeObjectURL(url);
        setIsTTSPlaying(false);
        dispatch(setIsTTSPlayingAction(false)); // Update Redux state
        playNext();
      };

      audio.play().then(() => {
        console.log('Audio is playing.');
      }).catch((e) => {
        console.error('Audio play error:', e);
        playNext();
      });
    };

    const handleMessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        if (isFirstMessage.current) {
          // Attempt to parse the first binary message as JSON format info
          try {
            const decoder = new TextDecoder('utf-8');
            const jsonString = decoder.decode(event.data);
            const message = JSON.parse(jsonString);

            if (message.type === 'format' && SUPPORTED_FORMATS.includes(message.format)) {
              audioFormat.current = message.format;
              console.log('Received audio format:', audioFormat.current);
            } else {
              console.error('Invalid or unsupported format information received:', message);
            }
          } catch (e) {
            console.error('Error parsing format message:', e);
          }
          isFirstMessage.current = false;
          return;
        }

        const arrayBuffer = event.data;
        console.log('Received audio chunk of size:', arrayBuffer.byteLength);

        if (arrayBuffer.byteLength === 0) {
          // End of audio stream indicator received
          console.log('Received end of audio stream.');
          setIsTTSPlaying(false);
          dispatch(setIsTTSPlayingAction(false)); // Update Redux state
          isPlayingRef.current = false;
          return;
        }

        audioQueue.current.push(arrayBuffer);
        if (!isPlayingRef.current) {
          isPlayingRef.current = true;
          playNext();
        }
      }
    };

    const initializeWebSocket = () => {
      try {
        ws = new WebSocket('ws://localhost:8000/ws/audio');
        ws.binaryType = 'arraybuffer';
        wsRef.current = ws; // Store WebSocket reference

        ws.onopen = () => {
          console.log('Audio WebSocket connection established.');
          setIsConnected(true);
        };

        ws.onmessage = handleMessage;

        ws.onerror = (error) => {
          console.error('Audio WebSocket error:', error);
        };

        ws.onclose = (event) => {
          console.log('Audio WebSocket closed:', event);
          isPlayingRef.current = false;
          setIsTTSPlaying(false);
          dispatch(setIsTTSPlayingAction(false)); // Update Redux state
          setIsConnected(false);
          wsRef.current = null;
        };
      } catch (e) {
        console.error('Audio WebSocket initialization error:', e);
      }
    };

    initializeWebSocket();

    // Cleanup on component unmount or when userInteracted changes
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [userInteracted, stopCurrentTTS, dispatch]);

  return { stopCurrentTTS, isTTSPlaying, isConnected };
};

export default useAudioPlayer;