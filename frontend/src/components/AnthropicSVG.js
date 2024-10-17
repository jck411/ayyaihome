// src/components/AnthropicSVG.js
import React from 'react';

const AnthropicSVG = ({ width = 24, height = 24, fill = 'currentColor' }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={width}
    height={height}
    viewBox="0 0 50 50"
    fill={fill}
  >
    <path d="M 5 5 L 5 45 L 45 45 L 45 5 L 5 5 z M 7 7 L 43 7 L 43 43 L 7 43 L 7 7 z M 20.03125 16.96875 L 14.03125 32.96875 L 17.5625 32.96875 L 18.648438 29.935547 L 25.253906 29.935547 L 26.306641 33.03125 L 29.818359 33.03125 L 23.722656 16.96875 L 20.03125 16.96875 z M 26.777344 16.978516 L 32.642578 33.015625 L 35.96875 33.015625 L 30.033203 16.978516 C 30.033203 16.978516 26.801344 16.954516 26.777344 16.978516 z M 21.966797 20.96875 L 24.041016 26.648438 L 19.765625 26.648438 L 21.966797 20.96875 z"></path>
  </svg>
);

export default AnthropicSVG;