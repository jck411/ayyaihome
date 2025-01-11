import React, { useState, useEffect, useRef } from 'react';
import { Send, Settings, Loader2, Mic, MicOff, Volume2, VolumeX, X, Check, Square } from 'lucide-react';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStoppingGeneration, setIsStoppingGeneration] = useState(false);

  // TTS (backend) toggle
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [isTogglingTTS, setIsTogglingTTS] = useState(false);

  // STT states
  const [isSttOn, setIsSttOn] = useState(false);
  const [isTogglingSTT, setIsTogglingSTT] = useState(false);
  const [sttTranscript, setSttTranscript] = useState('');

  // GPT response generation state
  const [isGenerating, setIsGenerating] = useState(false);

  // WebSocket connection status
  const [wsConnectionStatus, setWsConnectionStatus] = useState('disconnected');

  // Refs for WebSocket and messages
  const messagesEndRef = useRef(null);
  const websocketRef = useRef(null);
  const messagesRef = useRef(messages);

  // Update messagesRef whenever messages change
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // WebSocket setup
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/chat');
    websocketRef.current = ws;

    setWsConnectionStatus('connecting');

    ws.onopen = () => {
      console.log('Connected to Unified Chat WebSocket');
      setWsConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.stt_text) {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now(),
              sender: 'user',
              text: data.stt_text,
              timestamp: new Date().toLocaleTimeString(),
            },
          ]);

          setIsGenerating(true);
          websocketRef.current.send(
            JSON.stringify({
              action: 'chat',
              messages: [
                ...messagesRef.current,
                {
                  id: Date.now(),
                  sender: 'user',
                  text: data.stt_text,
                  timestamp: new Date().toLocaleTimeString(),
                },
              ],
            }),
          );
        }

        if (data.content) {
          const content = data.content;
          console.log(`Received GPT content: ${content}`);
          
          if (data.done === true) {
            setIsGenerating(false);
          }
          
          setMessages((prev) => {
            const lastIndex = prev.length - 1;
            if (prev[lastIndex] && prev[lastIndex].sender === 'assistant') {
              const updatedMessage = {
                ...prev[lastIndex],
                text: prev[lastIndex].text + content,
              };
              return [...prev.slice(0, lastIndex), updatedMessage];
            } else {
              return [
                ...prev,
                {
                  id: Date.now(),
                  sender: 'assistant',
                  text: content,
                  timestamp: new Date().toLocaleTimeString(),
                },
              ];
            }
          });
        }

        if (data.is_listening !== undefined) {
          setIsSttOn(data.is_listening);
          console.log(`STT is now ${data.is_listening ? 'ON' : 'OFF'}`);
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('Unified Chat WebSocket error:', error);
      setWsConnectionStatus('disconnected');
    };

    ws.onclose = () => {
      console.log('Unified Chat WebSocket closed');
      setWsConnectionStatus('disconnected');
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleStop = async () => {
    setIsStoppingGeneration(true);
    try {
      const response = await fetch('http://localhost:8000/api/stop', {
        method: 'POST',
      });

      if (response.ok) {
        console.log('Successfully stopped generation and TTS');
        setIsGenerating(false);
      } else {
        console.error('Failed to stop generation');
      }
    } catch (error) {
      console.error('Error stopping generation:', error);
    } finally {
      setIsStoppingGeneration(false);
    }
  };

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

  const toggleSTT = async () => {
    setIsTogglingSTT(true);
    try {
      if (!isSttOn) {
        websocketRef.current.send(JSON.stringify({ action: 'start-stt' }));
        console.log('Sent action: start-stt');
      } else {
        websocketRef.current.send(JSON.stringify({ action: 'pause-stt' }));
        console.log('Sent action: pause-stt');
      }
    } catch (error) {
      console.error('Error toggling STT:', error);
    } finally {
      setIsTogglingSTT(false);
    }
  };

  const handleSend = async (userInput) => {
    if (!userInput.trim()) return;

    const newMessage = {
      id: Date.now(),
      sender: 'user',
      text: userInput,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputMessage('');
    setSttTranscript('');

    setIsGenerating(true);
    try {
      const aiMessageId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        {
          id: aiMessageId,
          sender: 'assistant',
          text: '',
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);

      websocketRef.current.send(
        JSON.stringify({ action: 'chat', messages: [...messagesRef.current, newMessage] }),
      );
      console.log('Sent action: chat with messages:', [...messagesRef.current, newMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* TOP BAR */}
      <div className="bg-white shadow-sm p-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold text-gray-800">STT + TTS Chat</h1>
        <div className="flex items-center gap-4">
          {/* WebSocket Connection Status */}
          <div
            title={wsConnectionStatus}
            className="flex items-center gap-1"
          >
            {wsConnectionStatus === 'connected' ? (
              <div className="text-green-500">
                <Check className="w-4 h-4" />
              </div>
            ) : wsConnectionStatus === 'disconnected' ? (
              <div className="text-red-500">
                <X className="w-4 h-4" />
              </div>
            ) : (
              <div className="text-yellow-500">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            )}
            <span className="text-sm text-gray-600">{wsConnectionStatus}</span>
          </div>

          {/* Stop Button */}
          {isGenerating && (
            <button
              onClick={handleStop}
              disabled={isStoppingGeneration}
              className={`p-2 hover:bg-gray-100 rounded-full flex items-center gap-2 transition-all duration-200 
                ${isStoppingGeneration ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              title="Stop Generation and TTS"
            >
              {isStoppingGeneration ? (
                <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
              ) : (
                <Square className="w-5 h-5 text-red-500" fill="currentColor" />
              )}
            </button>
          )}

          {/* TTS Toggle */}
          <button
            onClick={toggleTTS}
            disabled={isTogglingTTS}
            className={`p-2 hover:bg-gray-100 rounded-full flex items-center gap-2 transition-all duration-200 
              ${isTogglingTTS ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            title={ttsEnabled ? 'Text-to-Speech Enabled' : 'Text-to-Speech Disabled'}
          >
            {isTogglingTTS ? (
              <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
            ) : ttsEnabled ? (
              <Volume2 className="w-5 h-5 text-green-500" title="Backend TTS Enabled" />
            ) : (
              <VolumeX className="w-5 h-5 text-gray-400" title="Backend TTS Disabled" />
            )}
          </button>

          {/* STT Toggle */}
          <button
            onClick={toggleSTT}
            disabled={isTogglingSTT}
            className={`p-2 hover:bg-gray-100 rounded-full flex items-center gap-2 transition-all duration-200 
              ${isTogglingSTT ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            title={isSttOn ? 'STT is ON. Click to Pause' : 'STT is OFF. Click to Start'}
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
          <input
            type="text"
            value={sttTranscript || inputMessage}
            onChange={(e) => {
              setInputMessage(e.target.value);
              setSttTranscript('');
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