// /home/jack/ayyaihome/frontend/src/MessageLogic.js

import { useState, useCallback, useRef, useEffect } from 'react';
import { generateChatResponse } from './services/chatService';

export const useMessageLogic = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("Online");
  const [selectedAPI, setSelectedAPI] = useState('anthropic');

  // Use useRef to keep track of the current WebSocket connection
  const currentWebSocketRef = useRef(null);
  // Use useRef to accumulate incoming content
  const assistantMessageBuffer = useRef("");

  const sendStopSignal = useCallback(() => {
    if (currentWebSocketRef.current) {
      currentWebSocketRef.current.close();
      console.log('WebSocket connection closed for stop signal');
      currentWebSocketRef.current = null;
      assistantMessageBuffer.current = "";  // Reset the buffer
    }
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const timestamp = new Date().toLocaleTimeString();
    const userMessage = { id: messages.length + 1, text: input, sender: "user", timestamp };

    console.log('User message sent:', userMessage);

    const context = [...messages, userMessage];
    console.log('Context being sent to API:', context);

    setMessages(context);
    setInput("");
    setStatus("Listening...");

    assistantMessageBuffer.current = "";  // Reset buffer for new message

    try {
      sendStopSignal();  // Close any existing WebSocket connection

      // Use the unified chat service
      await generateChatResponse(context, selectedAPI, (content) => {
        updateMessages(content, userMessage.id);
      }, (ws) => { currentWebSocketRef.current = ws; });

      setStatus("Online");
      currentWebSocketRef.current = null;  // Clear the WebSocket reference when done
    } catch (error) {
      console.error('Error:', error);
      setStatus("Offline");
      // Optionally, add an error message to the messages
      setMessages(prevMessages => [
        ...prevMessages,
        {
          id: prevMessages.length + 1,
          text: `Error: ${error.message}`,
          sender: "error",
          timestamp: new Date().toLocaleTimeString(),
        }
      ]);
    }
  };

  const updateMessages = (content, messageId) => {
    // Accumulate the content
    assistantMessageBuffer.current += content;

    setMessages((prevMessages) => {
      const updatedMessages = [...prevMessages];
      const existingAssistantMessage = updatedMessages.find(
        (msg) => msg.sender === "assistant" && msg.id === messageId + 1
      );

      if (existingAssistantMessage) {
        existingAssistantMessage.text = assistantMessageBuffer.current;
      } else {
        const newAssistantMessage = {
          id: messageId + 1,
          text: assistantMessageBuffer.current,
          sender: "assistant",
          timestamp: new Date().toLocaleTimeString(),
          metadata: { assistantType: selectedAPI }
        };
        updatedMessages.push(newAssistantMessage);
      }

      return updatedMessages;
    });
  };

  // Handle API switch by closing existing WebSocket
  useEffect(() => {
    sendStopSignal();
    // Optionally, initiate a new WebSocket connection if needed
  }, [selectedAPI, sendStopSignal]);

  return {
    messages,
    input,
    setInput,
    status,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    sendStopSignal,
  };
};
