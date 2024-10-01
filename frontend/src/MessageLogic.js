// /home/jack/ayyaihome/frontend/src/MessageLogic.js

import { useState, useCallback } from 'react';
import { generateAIResponse } from './services/openaiService';
import { generateAnthropicResponse } from './services/anthropicService';

export const useMessageLogic = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("Online");
  const [selectedAPI, setSelectedAPI] = useState('openai');
  const [loggedInUser, setLoggedInUser] = useState('guest');  // State to track the logged-in user
  const [ttsEnabled, setTtsEnabled] = useState(true);  // New state to track TTS toggle

  const [currentRequestId, setCurrentRequestId] = useState(null);  // Store the current request ID

  const sendStopSignal = useCallback(async () => {
    try {
      console.log('Sending stop signal...');
      if (!currentRequestId) {
        console.error('No current request ID to stop.');
        return;
      }
      const response = await fetch('http://localhost:8000/api/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: currentRequestId }),
      });
      if (!response.ok) {
        console.error('Failed to send stop signal');
      } else {
        console.log('Stop signal sent successfully');
        setCurrentRequestId(null);  // Clear the current request ID
      }
    } catch (error) {
      console.error('Error sending stop signal:', error);
    }
  }, [currentRequestId]);

  // Function to send a message and handle the API response
  const sendMessage = async () => {
    if (!input.trim()) return;

    const timestamp = new Date().toLocaleTimeString();

    // Append the logged-in user's name to the message text and add metadata
    const userMessage = { 
      id: messages.length + 1, 
      text: input,
      sender: "user", 
      timestamp,
      metadata: { user: loggedInUser || "Anonymous" }  // Only add metadata for the logged-in user
    };

    console.log('User message sent:', userMessage);  // Log user message

    const context = [...messages, userMessage];  // Create the context with previous messages and user message
    setMessages(context);
    setInput("");
    setStatus("Listening...");

    try {
      await sendStopSignal();  // Stop any previous request

      if (selectedAPI === 'openai') {
        await generateAIResponse(context, (content, isComplete = false, requestId = null) => {
          if (requestId) {
            setCurrentRequestId(requestId);  // Store the request ID
          }
          if (isComplete) {
            setCurrentRequestId(null);  // Clear the request ID when complete
          }
          updateMessages(content, userMessage.id, isComplete);
        }, ttsEnabled);  // Pass ttsEnabled to OpenAI service
      } else if (selectedAPI === 'anthropic') {
        await generateAnthropicResponse(context, (content, isComplete = false, requestId = null) => {
          if (requestId) {
            setCurrentRequestId(requestId);  // Store the request ID
          }
          if (isComplete) {
            setCurrentRequestId(null);  // Clear the request ID when complete
          }
          updateMessages(content, userMessage.id, isComplete);
        }, ttsEnabled);  // Pass ttsEnabled to Anthropic service
      }

      setStatus("Online");
    } catch (error) {
      console.error('Error:', error);
      setStatus("Offline");
    }
  };

  const updateMessages = (content, messageId, isComplete = false) => {
    setMessages((prevMessages) => {
      const updatedMessages = [...prevMessages];
      const existingAssistantMessage = updatedMessages.find(
        (msg) => msg.sender === "assistant" && msg.id === messageId + 1
      );

      if (existingAssistantMessage) {
        existingAssistantMessage.text = content;
      } else {
        const newAssistantMessage = {
          id: messageId + 1,
          text: content,
          sender: "assistant",
          timestamp: new Date().toLocaleTimeString(),
          metadata: { assistantType: selectedAPI === "anthropic" ? "anthropic" : "openai" }
        };
        updatedMessages.push(newAssistantMessage);
      }

      return updatedMessages;
    });
  };

  return {
    messages,
    input,
    setInput,
    status,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    sendStopSignal,
    setLoggedInUser,
    ttsEnabled,           // Expose TTS toggle state
    setTtsEnabled         // Expose function to toggle TTS
  };
};
