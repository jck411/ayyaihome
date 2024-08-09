// App.js
import React, { useState, useEffect } from 'react';
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

    const timestamp = new Date().toLocaleTimeString();
    const userMessage = { id: messages.length + 1, text: input, sender: "user", timestamp };
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
            updatedMessages.push({ id: userMessage.id + 1, text: content, sender: "assistant", timestamp: new Date().toLocaleTimeString() });
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

  // Function to send stop signal
  const sendStopSignal = async () => {
    try {
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
  };

  // Listen for "Enter" key press to trigger stop signal
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Enter") {
        sendStopSignal();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    // Cleanup event listener on component unmount
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  // Function to scroll to a specific AI message
  const scrollToAIMessage = (id) => {
    const element = document.getElementById(`ai-message-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div className={`min-h-screen w-full ${darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'}`}>
      <div className="max-w-[1000px] mx-auto p-4 flex flex-col h-screen">
        <div className="flex justify-between items-center mb-4">
          <StatusBar status={status} />
          <ModeToggle darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        </div>
        <div className="flex flex-grow overflow-hidden">
          <div className="flex-1 flex flex-col overflow-hidden pr-2">
            <MessageList 
              messages={messages} 
              sender="user" 
              onMessageClick={scrollToAIMessage} 
            />
          </div>
          <div className="flex-1 flex flex-col overflow-hidden pl-2">
            <MessageList messages={messages} sender="assistant" />
          </div>
        </div>
        <MessageInput input={input} setInput={setInput} sendMessage={sendMessage} darkMode={darkMode} />
      </div>
    </div>
  );
};

export default ChatWebsite;
