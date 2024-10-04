import { useState } from 'react';
import { generateAIResponse } from './services/openaiService';
import { generateAnthropicResponse } from './services/anthropicService';

export const useMessageLogic = () => {
  // State to manage the list of messages
  const [messages, setMessages] = useState([]);
  // State to manage the user input
  const [input, setInput] = useState("");
  // State to manage the status (e.g., Online, Listening, Offline)
  const [status, setStatus] = useState("Online");
  // State to track which API is selected (openai or anthropic)
  const [selectedAPI, setSelectedAPI] = useState('openai');
  // State to track the logged-in user
  const [loggedInUser, setLoggedInUser] = useState('guest');
  // State to track whether TTS (Text-to-Speech) is enabled
  const [ttsEnabled, setTtsEnabled] = useState(true);

  // Function to send a message and handle the API response
  const sendMessage = async () => {
    // Do nothing if the input is empty or contains only whitespace
    if (!input.trim()) return;

    // Generate a timestamp for the message
    const timestamp = new Date().toLocaleTimeString();

    // Create the user message object with metadata
    const userMessage = {
      id: messages.length + 1,
      text: input,
      sender: "user",
      timestamp,
      metadata: { user: loggedInUser || "Anonymous" }  // Add metadata for the logged-in user
    };

    console.log('User message sent:', userMessage);  // Log the user message

    // Add the user message to the current context (message history)
    const context = [...messages, userMessage];
    setMessages(context);  // Update the state with the new message
    setInput("");  // Clear the input field
    setStatus("Listening...");  // Update status to indicate the assistant is processing

    try {
      // Call the appropriate API based on the selected option
      if (selectedAPI === 'openai') {
        await generateAIResponse(context, (content, isComplete = false) => {
          // Update messages with the assistant's response
          updateMessages(content, userMessage.id, isComplete);
        }, ttsEnabled);  // Pass TTS status to OpenAI service
      } else if (selectedAPI === 'anthropic') {
        await generateAnthropicResponse(context, (content, isComplete = false) => {
          // Update messages with the assistant's response
          updateMessages(content, userMessage.id, isComplete);
        }, ttsEnabled);  // Pass TTS status to Anthropic service
      }

      setStatus("Online");  // Update status to indicate the assistant is ready
    } catch (error) {
      console.error('Error:', error);  // Log any errors
      setStatus("Offline");  // Update status to indicate an error occurred
    }
  };

  // Function to update the messages state with the assistant's response
  const updateMessages = (content, messageId, isComplete = false) => {
    setMessages((prevMessages) => {
      // Create a copy of the previous messages
      const updatedMessages = [...prevMessages];
      // Find if there is already an assistant message that needs updating
      const existingAssistantMessage = updatedMessages.find(
        (msg) => msg.sender === "assistant" && msg.id === messageId + 1
      );

      if (existingAssistantMessage) {
        // If an assistant message already exists, update its text
        existingAssistantMessage.text = content;
      } else {
        // If no assistant message exists, create a new one
        const newAssistantMessage = {
          id: messageId + 1,
          text: content,
          sender: "assistant",
          timestamp: new Date().toLocaleTimeString(),
          metadata: { assistantType: selectedAPI === "anthropic" ? "anthropic" : "openai" }  // Add metadata to indicate which API was used
        };
        updatedMessages.push(newAssistantMessage);  // Add the new assistant message
      }

      return updatedMessages;  // Return the updated list of messages
    });
  };

  // Return the state and functions to be used in the component
  return {
    messages,
    input,
    setInput,
    status,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    setLoggedInUser,
    ttsEnabled,           // Expose TTS toggle state
    setTtsEnabled         // Expose function to toggle TTS
  };
};