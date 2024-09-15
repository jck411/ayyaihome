import { useState, useCallback } from 'react';
import { generateAIResponse } from './services/openaiService';
import { generateAnthropicResponse } from './services/anthropicService';

export const useMessageLogic = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("Online");
  const [selectedAPI, setSelectedAPI] = useState('anthropic');

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
    const userMessage = { id: messages.length + 1, text: input, sender: "user", timestamp };
  
    console.log('User message sent:', userMessage); // Log user message
  
    const context = [...messages, userMessage]; // Create the context with previous messages and user message
    console.log('Context being sent to API:', context); // Log context sent to API
  
    setMessages(context);
    setInput("");
    setStatus("Listening...");
  
    try {
      await sendStopSignal();
  
      // Pass `selectedAPI` as an additional argument
      if (selectedAPI === 'openai') {
        await generateAIResponse(context, (content, isComplete) => {
          updateMessages(content, userMessage.id, isComplete);
        }, selectedAPI); // <-- Pass the selectedAPI here
      } else if (selectedAPI === 'anthropic') {
        await generateAnthropicResponse(context, (content, isComplete) => {
          updateMessages(content, userMessage.id, isComplete);
        }, selectedAPI); // <-- Pass the selectedAPI here
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
        console.log('Final assistant message:', existingAssistantMessage); // Log final message
      }
    } else {
      const newAssistantMessage = {
        id: messageId + 1,
        text: content,
        sender: "assistant",
        timestamp: new Date().toLocaleTimeString(),
        // Add metadata to indicate whether the response is from OpenAI or Anthropic
        metadata: { assistantType: selectedAPI === "anthropic" ? "anthropic" : "openai" }  // Here is the metadata
      };
      updatedMessages.push(newAssistantMessage);
      if (isComplete) {
        console.log('New assistant message added:', newAssistantMessage); // Log final message
      }
    }

    if (isComplete) {
      console.log('Updated messages:', updatedMessages); // Log full messages once completed
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
  };
};
