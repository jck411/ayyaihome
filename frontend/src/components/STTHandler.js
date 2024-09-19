import React, { useState, useEffect } from 'react';

const STTHandler = ({ isActive, onTranscription }) => {
  const [socket, setSocket] = useState(null);

  const startTranscription = () => {
    const newSocket = new WebSocket('ws://localhost:8000/ws/stt');

    newSocket.onopen = () => {
      console.log('WebSocket connection established');
    };

    newSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'transcribing' || data.type === 'transcribed') {
        onTranscription(data.text, data.type);
      } else if (data.type === 'info') {
        console.log(data.message);
      }
    };

    newSocket.onclose = () => {
      console.log('WebSocket connection closed');
    };

    setSocket(newSocket);
  };

  const stopTranscription = () => {
    if (socket) {
      socket.send('stop');
      socket.close();
    }
  };

  useEffect(() => {
    if (isActive) {
      startTranscription();
    } else {
      stopTranscription();
    }

    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [isActive]);

  return null; // No UI rendering here
};

export default STTHandler;
