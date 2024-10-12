import React from 'react';

const StopTTSButton = ({ isTTSPlaying, stopCurrentTTS }) => {
  return (
    <button
      onClick={stopCurrentTTS}
      className={`${
        isTTSPlaying ? 'bg-red-500 hover:bg-red-600' : 'bg-gray-400 cursor-not-allowed'
      } text-white p-3`}
      aria-label="Stop TTS"
      title="Stop TTS"
      disabled={!isTTSPlaying}
    >
      {/* "X" Icon */}
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none"
           viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"/>
      </svg>
    </button>
  );
};

export default StopTTSButton;