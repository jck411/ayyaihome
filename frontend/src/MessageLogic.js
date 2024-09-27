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

  const sendStopSignal = useCallback(async () => {
    try {
      console.log('Sending stop signal...');
      const response = await fetch('http://localhost:8000/api/stop', {
        method: 'POST',
      });
      if (!response.ok) {
        console.error('Failed to send stop signal');
      } else {
        console.log('Stop signal sent successfully');
      }
    } catch (error) {
      console.error('Error sending stop signal:', error);
    }
  }, []);

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
      await sendStopSignal();

      if (selectedAPI === 'openai') {
        await generateAIResponse(context, (content, isComplete) => {
          updateMessages(content, userMessage.id, isComplete);
        }, selectedAPI, ttsEnabled);  // Pass ttsEnabled to OpenAI service
      } else if (selectedAPI === 'anthropic') {
        await generateAnthropicResponse(context, (content, isComplete) => {
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