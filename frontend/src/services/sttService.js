// /home/jack/ayyaihome/frontend/src/services/sttService.js

import { useState, useEffect, useRef } from 'react';

const useSTTService = () => {
  const [sttInput, setSTTInput] = useState('');
  const [isSTTOn, setIsSTTOn] = useState(false);
  const websocketRef = useRef(null);

  useEffect(() => {
    // Prevent multiple WebSocket instances
    if (websocketRef.current) return;

    // Initialize WebSocket connection
    websocketRef.current = new WebSocket('ws://localhost:8000/ws/stt');

    websocketRef.current.onopen = () => {
      console.log('STT WebSocket connection opened');
    };

    websocketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'stt_result') {
          setSTTInput(data.text);
        }
      } catch (error) {
        console.error('Error parsing STT message:', error);
      }
    };

    websocketRef.current.onclose = () => {
      console.log('STT WebSocket connection closed');
    };

    websocketRef.current.onerror = (error) => {
      console.error('STT WebSocket error:', error);
    };

    return () => {
      // Don't close the WebSocket on unmount due to React Strict Mode
      // Instead, close it when the component actually unmounts in production
      // Check if the WebSocket is still open before closing
      if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
        websocketRef.current.close();
      }
    };
  }, []); // Empty dependency array ensures this runs once

  const startSTT = () => {
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ command: 'start_stt' }));
      setIsSTTOn(true);
    } else {
      console.error('WebSocket is not open');
    }
  };

  const stopSTT = () => {
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ command: 'stop_stt' }));
      setIsSTTOn(false);
    } else {
      console.error('WebSocket is not open');
    }
  };

  return { sttInput, setSTTInput, isSTTOn, startSTT, stopSTT };
};

export default useSTTService;
