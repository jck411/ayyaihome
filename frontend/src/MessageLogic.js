import { useState, useCallback } from 'react';
import { generateAIResponse } from './services/openaiService';
import { generateAnthropicResponse } from './services/anthropicService';

export const useMessageLogic = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("Online");
  const [selectedAPI, setSelectedAPI] = useState('anthropic');
  const [loggedInUser, setLoggedInUser] = useState(null);  // State to track the logged-in user

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
      text: input,  // No prefix in the message itself
      sender: "user", 
      timestamp,
      metadata: { user: loggedInUser || "Anonymous" }  // Only add metadata for the logged-in user
    };

    console.log('User message sent:', userMessage);  // Log user message

    const context = [...messages, userMessage];  // Create the context with previous messages and user message
    console.log('Context being sent to API:', context);  // Log context sent to API

    setMessages(context);
    setInput("");
    setStatus("Listening...");

    try {
      await sendStopSignal();

      // Pass `selectedAPI` as an additional argument
      if (selectedAPI === 'openai') {
        await generateAIResponse(context, (content, isComplete) => {
          updateMessages(content, userMessage.id, isComplete);
        }, selectedAPI);
      } else if (selectedAPI === 'anthropic') {
        await generateAnthropicResponse(context, (content, isComplete) => {
          updateMessages(content, userMessage.id, isComplete);
        }, selectedAPI);
      }

      setStatus("Online");
    } catch (error) {
      console.error('Error:', error);
      setStatus("Offline");
    }
  };

  // Function to update messages based on API response
  const updateMessages = (content, messageId, isComplete = false) => {
    setMessages((prevMessages) => {
      const updatedMessages = [...prevMessages];
      const existingAssistantMessage = updatedMessages.find(
        (msg) => msg.sender === "assistant" && msg.id === messageId + 1
      );

      if (existingAssistantMessage) {
        existingAssistantMessage.text = content;
        if (isComplete) {
          console.log('Final assistant message:', existingAssistantMessage);  // Log final message
        }
      } else {
        const newAssistantMessage = {
          id: messageId + 1,
          text: content,
          sender: "assistant",
          timestamp: new Date().toLocaleTimeString(),
          metadata: { assistantType: selectedAPI === "anthropic" ? "anthropic" : "openai" }  // Metadata for assistants
        };
        updatedMessages.push(newAssistantMessage);
        if (isComplete) {
          console.log('New assistant message added:', newAssistantMessage);  // Log final message
        }
      }

      if (isComplete) {
        console.log('Updated messages:', updatedMessages);  // Log full messages once completed
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
    setLoggedInUser  // Function to log in a user
  };
};
