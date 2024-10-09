// /home/jack/ayyaihome/frontend/src/hooks/useWebSocket.js

import { useEffect, useState, useRef } from "react";

const useWebSocket = (url) => {
  const [message, setMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const websocketRef = useRef(null);

  useEffect(() => {
    // Create a new WebSocket connection when the component mounts
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

    // Cleanup function to close WebSocket connection when component unmounts
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [url]);

  return { message, isConnected };
};

export default useWebSocket;
