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
      const response = await fetch('http://localhost:8000/api/stop', {
        method: 'POST',
      });
      if (!response.ok) {
        // Handle stop signal failure
      }
    } catch (error) {
      // Handle stop signal error
    }
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      id: `msg_${Date.now()}`,
      type: "message",
      role: "user",
      content: [{ type: "text", text: input }],
      timestamp: new Date().toLocaleTimeString()  // Add timestamp to user message
    };

    if (selectedAPI === 'openai') {
      setOpenaiMessages((prevMessages) => [...prevMessages, userMessage]);
    } else if (selectedAPI === 'anthropic') {
      setAnthropicMessages((prevMessages) => [...prevMessages, userMessage]);
    }

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
      setStatus("Offline");
    }
  };

  const updateMessages = (content, messageId, isComplete = false, api) => {
    const setContext = api === 'openai' ? setOpenaiMessages : setAnthropicMessages;

    setContext((prevMessages) => {
      const updatedMessages = [...prevMessages];
      const existingAssistantMessage = updatedMessages.find(
        (msg) => msg.role === "assistant" && msg.id === `msg_${parseInt(messageId.split('_')[1]) + 1}`
      );

      if (existingAssistantMessage) {
        existingAssistantMessage.content[0].text = content;
      } else {
        const newAssistantMessage = {
          id: `msg_${parseInt(messageId.split('_')[1]) + 1}`,
          type: "message",
          role: "assistant",
          content: [{ type: "text", text: content }],
          timestamp: new Date().toLocaleTimeString()  // Add timestamp to assistant message
        };
        updatedMessages.push(newAssistantMessage);
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
