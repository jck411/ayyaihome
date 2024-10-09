// /home/jack/ayyaihome/frontend/src/components/KeywordListener.js

import React, { useEffect } from "react";
import useWebSocket from "../hooks/useWebSocket";

const KeywordListener = () => {
  // Connect to the /ws/keyword WebSocket endpoint
  const { message, isConnected } = useWebSocket("ws://localhost:8000/ws/keyword");

  useEffect(() => {
    if (message) {
      console.log("Keyword detected:", message);
      alert("Keyword detected: " + message);  // Optional: show alert when keyword is detected
    }
  }, [message]);

  useEffect(() => {
    console.log(`Keyword WebSocket is ${isConnected ? "connected" : "disconnected"}`);
  }, [isConnected]);

  return (
    <div>
      <h2>Keyword WebSocket Connection: {isConnected ? "Connected" : "Disconnected"}</h2>
      {message && <p>Keyword detected: {message}</p>}
    </div>
  );
};

export default KeywordListener;
