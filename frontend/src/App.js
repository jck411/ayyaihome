import React, { useState } from 'react';
import { generateAIResponse } from './services/openaiService';
import StatusBar from './components/StatusBar';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import ModeToggle from './components/ModeToggle';

const ChatWebsite = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("Online");

  const toggleDarkMode = () => setDarkMode(!darkMode);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { id: messages.length + 1, text: input, sender: "user" };
    setMessages([...messages, userMessage]);
    setInput("");
    setStatus("Listening...");

    console.log("Sending message:", userMessage);

    try {
      await generateAIResponse([...messages, userMessage], (content) => {
        console.log("Received content:", content);
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          const existingAssistantMessage = updatedMessages.find(msg => msg.sender === "assistant" && msg.id === userMessage.id + 1);

          if (existingAssistantMessage) {
            existingAssistantMessage.text = content;
          } else {
            updatedMessages.push({ id: userMessage.id + 1, text: content, sender: "assistant" });
          }

          return updatedMessages;
        });
      });
      setStatus("Online");
    } catch (error) {
      console.error('Error:', error);
      setStatus("Offline");
    }
  };

  return (
    <div className={`min-h-screen w-full ${darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'}`}>
      <div className="max-w-[1000px] mx-auto p-4 flex flex-col h-screen">
        <div className="flex justify-between items-center mb-4">
          <StatusBar status={status} />
          <ModeToggle darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        </div>
        <MessageList messages={messages} />
        <MessageInput input={input} setInput={setInput} sendMessage={sendMessage} darkMode={darkMode} />
      </div>
    </div>
  );
};

export default ChatWebsite;
