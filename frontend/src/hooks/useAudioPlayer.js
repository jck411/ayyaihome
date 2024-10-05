// frontend/src/hooks/useAudioPlayer.js

import { useEffect } from 'react';

const SUPPORTED_FORMATS = [
  'audio/mpeg',                    // MP3
  'audio/aac',                     // AAC
  'audio/ogg; codecs=opus',        // OPUS in OGG container
  'audio/webm; codecs=opus'        // OPUS in WebM container
];

const useAudioPlayer = () => {
  useEffect(() => {
    let ws;
    let audioFormat = 'audio/mpeg'; // Default format
    const audioQueue = [];
    let isPlaying = false;
    let isFirstMessage = true; // Flag to identify the first message

    const playNext = () => {
      if (audioQueue.length === 0) {
        isPlaying = false;
        return;
      }

      const audioData = audioQueue.shift();
      const blob = new Blob([audioData], { type: audioFormat });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);

      audio.onended = () => {
        URL.revokeObjectURL(url);
        playNext();
      };

      audio.onerror = (e) => {
        console.error('Audio playback error:', e);
        URL.revokeObjectURL(url);
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
      if (isFirstMessage && event.data instanceof ArrayBuffer) {
        // Attempt to parse the first binary message as JSON format info
        try {
          const decoder = new TextDecoder('utf-8');
          const jsonString = decoder.decode(event.data);
          const message = JSON.parse(jsonString);

          if (message.type === 'format' && SUPPORTED_FORMATS.includes(message.format)) {
            audioFormat = message.format;
            console.log('Received audio format:', audioFormat);
          } else {
            console.error('Invalid or unsupported format information received:', message);
          }
        } catch (e) {
          console.error('Error parsing format message:', e);
        }
        isFirstMessage = false;
        return;
      }

      if (event.data instanceof ArrayBuffer) {
        const arrayBuffer = event.data;
        console.log('Received audio chunk of size:', arrayBuffer.byteLength);

        if (arrayBuffer.byteLength === 0) {
          console.log('Received zero-length audio chunk, ignoring.');
          return;
        }

        audioQueue.push(arrayBuffer);
        if (!isPlaying) {
          isPlaying = true;
          playNext();
        }
      }
    };

    const initializeWebSocket = () => {
      try {
        ws = new WebSocket('ws://localhost:8000/ws/audio');
        ws.binaryType = 'arraybuffer';

        ws.onopen = () => {
          console.log('WebSocket connection established.');
        };

        ws.onmessage = handleMessage;

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = (event) => {
          console.log('WebSocket closed:', event);
        };
      } catch (e) {
        console.error('WebSocket initialization error:', e);
      }
    };

    initializeWebSocket();

    // Clean up on component unmount
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  return null; // This hook does not return a component
};

export default useAudioPlayer;
