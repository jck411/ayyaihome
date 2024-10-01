// /home/jack/ayyaihome/frontend/src/hooks/useAudioPlayer.js

import { useEffect } from 'react';

const useAudioPlayer = () => {
  useEffect(() => {
    let ws;

    try {
      ws = new WebSocket('ws://localhost:8000/ws/audio');
      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        console.log('WebSocket connection established');
      };

      const audioQueue = [];
      let isPlaying = false;

      const playNext = () => {
        if (audioQueue.length === 0) {
          isPlaying = false;
          return;
        }

        const audioData = audioQueue.shift();
        const blob = new Blob([audioData], { type: 'audio/mpeg' });
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
          console.log('Audio is playing');
        }).catch((e) => {
          console.error('Audio play error:', e);
          playNext();
        });
      };

      ws.onmessage = (event) => {
        const arrayBuffer = event.data;
        console.log('Received audio chunk of size:', arrayBuffer.byteLength);

        if (arrayBuffer.byteLength === 0) {
          console.log('Received zero-length audio chunk, ignoring.');
          // Optionally, insert a pause or skip
          return;
        }

        audioQueue.push(arrayBuffer);
        if (!isPlaying) {
          isPlaying = true;
          playNext();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event);
      };

    } catch (e) {
      console.error('WebSocket initialization error:', e);
    }

    // Clean up
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  return null; // This hook does not return a component
};

export default useAudioPlayer;
