// /home/jack/ayyaihome/frontend/src/hooks/useWebSocket.js

import { useEffect, useState, useRef, useCallback } from "react";

const useWebSocket = (url) => {
  const [message, setMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const websocketRef = useRef(null);

  // Function to connect to the WebSocket
  const connectWebSocket = useCallback(() => {
    if (!url) return;
    
    // Create a new WebSocket connection
    websocketRef.current = new WebSocket(url);

    // WebSocket open event
    websocketRef.current.onopen = () => {
      setIsConnected(true);
      console.log("WebSocket connection established.");
    };

    // WebSocket message event
    websocketRef.current.onmessage = (event) => {
      setMessage(event.data);
      console.log("Message received from WebSocket:", event.data);
    };

    // WebSocket close event
    websocketRef.current.onclose = () => {
      setIsConnected(false);
      console.log("WebSocket connection closed.");
    };

    // WebSocket error event
    websocketRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }, [url]);

  // Effect to manage the WebSocket connection lifecycle
  useEffect(() => {
    connectWebSocket();

    // Cleanup function to close WebSocket connection when component unmounts
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Function to send a message through the WebSocket
  const sendMessage = useCallback((msg) => {
    if (websocketRef.current && isConnected) {
      websocketRef.current.send(msg);
      console.log("Message sent to WebSocket:", msg);
    } else {
      console.warn("Cannot send message, WebSocket is not connected.");
    }
  }, [isConnected]);

  return { message, isConnected, sendMessage };
};

export default useWebSocket;