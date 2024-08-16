import React, { useState, useEffect } from 'react';
import { generateAIResponse } from './services/openaiService';
import { generateAnthropicResponse } from './services/anthropicService';
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import ModeToggle from './components/ModeToggle';

const ChatWebsite = () => {
  const [darkMode, setDarkMode] = useState(true);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("Online");
  const [selectedAPI, setSelectedAPI] = useState('anthropic');
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [leftWidth, setLeftWidth] = useState(33);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  const toggleSidebar = () => setSidebarOpen(!isSidebarOpen);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const timestamp = new Date().toLocaleTimeString();
    const userMessage = { id: messages.length + 1, text: input, sender: "user", timestamp };
    setMessages([...messages, userMessage]);
    setInput("");
    setStatus("Listening...");

    try {
      if (selectedAPI === 'openai') {
        await sendStopSignal();
        await generateAIResponse([...messages, userMessage], (content) => {
          updateMessages(content, userMessage.id);
        });
      } else if (selectedAPI === 'anthropic') {
        await generateAnthropicResponse([...messages, userMessage], (content) => {
          updateMessages(content, userMessage.id);
        });
      }

      setStatus("Online");
    } catch (error) {
      console.error('Error:', error);
      setStatus("Offline");
    }
  };

  const updateMessages = (content, messageId) => {
    setMessages((prevMessages) => {
      const updatedMessages = [...prevMessages];
      const existingAssistantMessage = updatedMessages.find(
        (msg) => msg.sender === "assistant" && msg.id === messageId + 1
      );

      if (existingAssistantMessage) {
        existingAssistantMessage.text = content;
      } else {
        updatedMessages.push({
          id: messageId + 1,
          text: content,
          sender: "assistant",
          timestamp: new Date().toLocaleTimeString(),
        });
      }

      return updatedMessages;
    });
  };

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

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Enter" && event.target.tagName !== "TEXTAREA") {
        event.preventDefault();
        if (selectedAPI === 'openai') {
          sendStopSignal();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [selectedAPI]);

  const scrollToAIMessage = (id) => {
    const element = document.getElementById(`ai-message-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const handleDrag = (e) => {
    const newLeftWidth = (e.clientX / window.innerWidth) * 100;
    if (newLeftWidth > 20 && newLeftWidth < 80) {
      setLeftWidth(newLeftWidth);
    }
  };

  const handleDragEnd = () => {
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', handleDragEnd);
  };

  const handleMouseDown = () => {
    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', handleDragEnd);
  };

  return (
    <div className={`min-h-screen w-full ${darkMode ? 'bg-dark-bg text-dark-text' : 'bg-light-bg text-light-text'}`}>
      <Sidebar
        isOpen={isSidebarOpen}
        toggleSidebar={toggleSidebar}
        selectedAPI={selectedAPI}
        setSelectedAPI={setSelectedAPI}
      />
      <div className="max-w-[1200px] mx-auto p-4 flex flex-col h-screen">
        <div className="flex justify-between items-center mb-4">
          <StatusBar status={status} toggleSidebar={toggleSidebar} />
          <ModeToggle darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        </div>
        <div className="flex flex-grow overflow-hidden">
          <div className="flex" style={{ width: `${leftWidth}%` }}>
            <MessageList
              messages={messages}
              sender="user"
              onMessageClick={scrollToAIMessage}
            />
          </div>
          <div
            className="mid-cursor"
            onMouseDown={handleMouseDown}
          />
          <div className="flex flex-col overflow-hidden" style={{ width: `${100 - leftWidth}%` }}>
            <MessageList messages={messages} sender="assistant" />
          </div>
        </div>
        <MessageInput input={input} setInput={setInput} sendMessage={sendMessage} darkMode={darkMode} />
      </div>
    </div>
  );
};

export default ChatWebsite;
