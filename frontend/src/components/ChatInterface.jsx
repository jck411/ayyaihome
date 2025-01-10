// ChatInterface.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Send, Settings, Loader2, Mic, MicOff } from 'lucide-react';

const generateAIResponse = async (messages, onContentStream) => {
  try {
    const endpoint = 'http://localhost:8000/api/chat';
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Request failed: ${errorText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      
      // Split the buffer by newlines and process each complete line
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep the last incomplete line in the buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.slice(6); // Remove 'data: ' prefix
            const data = JSON.parse(jsonStr);
            if (data.content) {
              onContentStream(data.content);
            }
          } catch (e) {
            console.error('Error parsing JSON:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error in generateAIResponse:', error);
    throw error;
  }
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');

  // TTS (backend) toggle
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [isTogglingTTS, setIsTogglingTTS] = useState(false);

  // STT states
  const [isSttOn, setIsSttOn] = useState(false);
  const [isTogglingSTT, setIsTogglingSTT] = useState(false);
  const [sttTranscript, setSttTranscript] = useState('');

  // GPT response generation state
  const [isGenerating, setIsGenerating] = useState(false);

  const messagesEndRef = useRef(null);
  const websocketRef = useRef(null);

  // ------------------- SCROLL TO BOTTOM WHEN MESSAGES UPDATE -------------------
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ------------------- FETCH INITIAL STT STATUS -------------------
  useEffect(() => {
    const fetchSttStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/stt/status');
        if (response.ok) {
          const data = await response.json();
          setIsSttOn(data.is_listening);
          console.log(`Initial STT status fetched: ${data.is_listening ? 'ON' : 'OFF'}`);
        }
      } catch (error) {
        console.error('Error fetching STT status:', error);
      }
    };

    fetchSttStatus();
  }, []);

  // ------------------- WEBSOCKET for AZURE STT from the SERVER -------------------
  useEffect(() => {
    // Open a WebSocket to receive recognized text from the server
    const ws = new WebSocket('ws://localhost:8000/ws/stt'); // Adjust if SSL => wss://
    websocketRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to STT WebSocket');
    };

    ws.onmessage = (event) => {
      // Each message is recognized text from the server
      const recognizedText = event.data;
      console.log(`Received STT text: ${recognizedText}`);
      // Append recognized text to sttTranscript
      setSttTranscript((prev) => prev + recognizedText + ' ');
    };

    ws.onerror = (error) => {
      console.error('STT WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('STT WebSocket closed');
    };

    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, []);

  // ------------------- HANDLE TTS TOGGLE -------------------
  const toggleTTS = async () => {
    setIsTogglingTTS(true);
    try {
      const response = await fetch('http://localhost:8000/api/toggle-tts', {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        setTtsEnabled(data.tts_enabled);
        console.log(`TTS toggled: ${data.tts_enabled ? 'Enabled' : 'Disabled'}`);
      } else {
        console.error('Failed to toggle TTS');
      }
    } catch (error) {
      console.error('Error toggling TTS:', error);
    } finally {
      setIsTogglingTTS(false);
    }
  };

  // ------------------- HANDLE STT TOGGLE -------------------
  const toggleSTT = async () => {
    setIsTogglingSTT(true);
    try {
      if (!isSttOn) {
        // Turn ON: call /api/stt/start
        const resp = await fetch('http://localhost:8000/api/stt/start', { method: 'POST' });
        if (!resp.ok) throw new Error('Failed to start STT');
        const data = await resp.json();
        setIsSttOn(data.is_listening);
        console.log('STT turned ON');
      } else {
        // Turn OFF: call /api/stt/pause
        const resp = await fetch('http://localhost:8000/api/stt/pause', { method: 'POST' });
        if (!resp.ok) throw new Error('Failed to pause STT');
        const data = await resp.json();
        setIsSttOn(data.is_listening);
        console.log('STT turned OFF');
      }
    } catch (error) {
      console.error('Error toggling STT:', error);
    } finally {
      setIsTogglingSTT(false);
    }
  };

  // ------------------- HANDLE SENDING USER INPUT TO GPT -------------------
  const handleSend = async (userInput) => {
    if (!userInput.trim()) return;

    const newMessage = {
      id: Date.now(),
      sender: 'user',
      text: userInput,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputMessage('');
    setSttTranscript(''); // Clear anything from the transcript now that it's "sent"

    if (!isGenerating) {
      setIsGenerating(true);
      try {
        const aiMessageId = Date.now() + 1;
        setMessages((prev) => [
          ...prev,
          {
            id: aiMessageId,
            sender: 'assistant',
            text: '',
            timestamp: new Date().toLocaleTimeString()
          }
        ]);

        await generateAIResponse([...messages, newMessage], (content) => {
          // Append new content to the assistant's message
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === aiMessageId 
                ? { ...msg, text: prev.find(m => m.id === aiMessageId).text + content }
                : msg
            )
          );
        });
        
      } catch (error) {
        console.error('Error sending message:', error);
      } finally {
        setIsGenerating(false);
      }
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* TOP BAR */}
      <div className="bg-white shadow-sm p-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold text-gray-800">STT + TTS Chat</h1>
        <div className="flex items-center gap-4">
          {/* TTS Toggle */}
          <button
            onClick={toggleTTS}
            disabled={isTogglingTTS}
            className={`p-2 hover:bg-gray-100 rounded-full flex items-center gap-2 transition-all duration-200 
              ${isTogglingTTS ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            title={ttsEnabled ? "Text-to-Speech Enabled" : "Text-to-Speech Disabled"}
          >
            {isTogglingTTS ? (
              <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
            ) : ttsEnabled ? (
              // Assuming Volume2 and VolumeX indicate backend TTS status
              <span title="Backend TTS Enabled">🔊</span> // You can replace with appropriate icons
            ) : (
              <span title="Backend TTS Disabled">🔇</span> // You can replace with appropriate icons
            )}
          </button>

          {/* STT Toggle */}
          <button
            onClick={toggleSTT}
            disabled={isTogglingSTT}
            className={`p-2 hover:bg-gray-100 rounded-full flex items-center gap-2 transition-all duration-200 
              ${isTogglingSTT ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            title={isSttOn ? "STT is ON. Click to Pause" : "STT is OFF. Click to Start"}
          >
            {isTogglingSTT ? (
              <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
            ) : isSttOn ? (
              <Mic className="w-5 h-5 text-green-500" />
            ) : (
              <MicOff className="w-5 h-5 text-gray-400" />
            )}
          </button>

          {/* Settings placeholder */}
          <button className="p-2 hover:bg-gray-100 rounded-full flex items-center gap-2 transition-all duration-200">
            <Settings className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>

      {/* MESSAGES AREA */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                message.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800'
              } shadow-sm`}
            >
              <div className="text-sm whitespace-pre-wrap">{message.text}</div>
              <div
                className={`text-xs mt-1 ${
                  message.sender === 'user' ? 'text-blue-100' : 'text-gray-400'
                }`}
              >
                {message.timestamp}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* INPUT + SEND */}
      <div className="border-t bg-white p-4">
        <div className="flex items-center gap-4 max-w-4xl mx-auto">
          {/* Show recognized speech or typed text */}
          <input
            type="text"
            value={sttTranscript || inputMessage}
            onChange={(e) => {
              // If user is typing manually, store it in inputMessage.
              setInputMessage(e.target.value);
              setSttTranscript(''); // Clear if user is manually typing
            }}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && (inputMessage.trim() || sttTranscript.trim())) {
                handleSend(sttTranscript || inputMessage);
              }
            }}
            placeholder="Type or speak your message..."
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={() => handleSend(sttTranscript || inputMessage)}
            disabled={isGenerating}
            className={`p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 
              ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isGenerating ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
