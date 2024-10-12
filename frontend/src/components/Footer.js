// src/components/Footer.js
import React from 'react';
import MessageInput from './MessageInput';
import StopTTSButton from './StopTTSButton';

const Footer = ({ appLogic }) => {
  const {
    input,
    setInput,
    sendMessage,
    darkMode,
    stopCurrentTTS,
    isTTSPlaying,
  } = appLogic;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 p-4">
      <div className="mx-auto" style={{ maxWidth: '600px', width: '100%' }}>
        <MessageInput
          input={input}
          setInput={setInput}
          sendMessage={sendMessage}
          darkMode={darkMode}
          stopCurrentTTS={stopCurrentTTS}
        />
      </div>
      <div className="fixed bottom-20 right-4 z-50">
        <StopTTSButton isTTSPlaying={isTTSPlaying} stopCurrentTTS={stopCurrentTTS} />
      </div>
    </div>
  );
};

export default Footer;
