import { useState, useCallback } from 'react';
import { generateAIResponse } from './services/openaiService';
import { generateAnthropicResponse } from './services/anthropicService';

export const useMessageLogic = () => {
  const [openaiMessages, setOpenaiMessages] = useState([]);
  const [anthropicMessages, setAnthropicMessages] = useState([]);
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
    const userMessage = { id: Date.now(), text: input, sender: "user", timestamp };

    // Update the context directly without assigning to 'context' variable
    if (selectedAPI === 'openai') {
      setOpenaiMessages((prevMessages) => [...prevMessages, userMessage]);
    } else if (selectedAPI === 'anthropic') {
      setAnthropicMessages((prevMessages) => [...prevMessages, userMessage]);
    }

    console.log('User message sent:', userMessage);  // Log user message

    setInput("");
    setStatus("Listening...");

    try {
      await sendStopSignal();
      if (selectedAPI === 'openai') {
        await generateAIResponse([...openaiMessages, userMessage], (content, isComplete) => {
          updateMessages(content, userMessage.id, isComplete, 'openai');
        });
      } else if (selectedAPI === 'anthropic') {
        await generateAnthropicResponse([...anthropicMessages, userMessage], (content, isComplete) => {
          updateMessages(content, userMessage.id, isComplete, 'anthropic');
        });
      }
      setStatus("Online");
    } catch (error) {
      console.error('Error:', error);
      setStatus("Offline");
    }
  };

  // Function to update messages based on API response
  const updateMessages = (content, messageId, isComplete = false, api) => {
    const setContext = api === 'openai' ? setOpenaiMessages : setAnthropicMessages;

    setContext((prevMessages) => {
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
    openaiMessages,
    anthropicMessages,
    input,
    setInput,
    status,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    sendStopSignal,
  };
};
