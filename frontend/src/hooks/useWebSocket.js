import { useEffect, useState, useRef, useCallback } from "react";
import { useDispatch } from 'react-redux';
import { setKeyword, setKeywordConnectionStatus } from '../slices/keywordSlice';

const useWebSocket = (url) => {
  const [message, setMessage] = useState(null);
  const websocketRef = useRef(null);
  const dispatch = useDispatch(); // Get dispatch function

  // Function to connect to the WebSocket
  const connectWebSocket = useCallback(() => {
    if (!url) return;

    // Create a new WebSocket connection
    websocketRef.current = new WebSocket(url);

    // WebSocket open event
    websocketRef.current.onopen = () => {
      console.log("WebSocket connection established.");
      dispatch(setKeywordConnectionStatus(true));  // Dispatch connection status to Redux
    };

    // WebSocket message event
    websocketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessage(data);
        console.log("Message received from WebSocket:", data);
        if (data.keyword) {
          // Dispatch setKeyword action with the received keyword and timestamp
          dispatch(setKeyword({ keyword: data.keyword, timestamp: data.timestamp }));
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    // WebSocket close event
    websocketRef.current.onclose = () => {
      console.log("WebSocket connection closed.");
      dispatch(setKeywordConnectionStatus(false));  // Dispatch disconnection status to Redux
    };

    // WebSocket error event
    websocketRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }, [url, dispatch]);

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

  return { message };  // Return only the message, no need for sendMessage if not used
};

export default useWebSocket;
