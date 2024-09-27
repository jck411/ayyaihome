// Path: frontend/src/components/MicrophoneTest.js

import React, { useEffect } from 'react';

const MicrophoneTest = () => {
  useEffect(() => {
    // Request microphone access
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const microphone = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        microphone.connect(analyser);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const getMicrophoneVolume = () => {
          analyser.getByteFrequencyData(dataArray);
          const volume = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
          console.log('Microphone volume:', volume); // Log microphone input volume
          requestAnimationFrame(getMicrophoneVolume);
        };

        getMicrophoneVolume();
      })
      .catch((error) => {
        console.error('Error accessing the microphone:', error);
      });
  }, []);

  return <div>Check the console for microphone volume data.</div>;
};

export default MicrophoneTest;
