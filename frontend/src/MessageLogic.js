import { useState, useCallback, useRef } from 'react';
import { generateAIResponse } from './services/openaiService';
import { generateAnthropicResponse } from './services/anthropicService';

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

      // Pass `setWebSocket` as the fourth argument
      if (selectedAPI === 'openai') {
        await generateAIResponse(context, (content) => {
          updateMessages(content, userMessage.id);
        }, selectedAPI, (ws) => { currentWebSocketRef.current = ws; });
      } else if (selectedAPI === 'anthropic') {
        await generateAnthropicResponse(context, (content) => {
          updateMessages(content, userMessage.id);
        }, selectedAPI, (ws) => { currentWebSocketRef.current = ws; });
      }

      setStatus("Online");
      currentWebSocketRef.current = null;  // Clear the WebSocket reference when done
    } catch (error) {
      console.error('Error:', error);
      setStatus("Offline");
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
