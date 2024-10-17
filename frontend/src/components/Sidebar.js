// src/components/Sidebar.js
import React from 'react';
import { FaMicrophone, FaCog } from 'react-icons/fa';
import OpenAISVG from './OpenAISVG';
import AnthropicSVG from './AnthropicSVG';

const Sidebar = ({
  isOpen,
  selectedAPI,
  setSelectedAPI,
  darkMode,
  ttsEnabled,
  setTtsEnabled,
}) => {
  const apiOptions = [
    { id: 'openai', label: 'OpenAI', icon: <OpenAISVG width={20} height={20} /> },
    { id: 'anthropic', label: 'Anthropic', icon: <AnthropicSVG width={20} height={20} /> },
    { id: 'o1', label: 'o1-Model', icon: <OpenAISVG width={20} height={20} /> }, // 'o1' in lowercase
  ];

  return (
    <div
      className={`fixed left-0 top-0 z-40 transition-transform transform ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
      style={{
        top: 'var(--status-bar-height)',
        height: 'calc(100% - var(--status-bar-height))',
        width: '250px',
        backgroundColor: darkMode ? 'var(--dark-bg)' : 'var(--light-bg)',
        color: 'var(--contrast-orange)',
      }}
    >
      <div className="p-4">
        {/* TTS Toggle */}
        <div className="mt-4">
          <h2 className="font-bold text-contrast-orange flex items-center">
            <FaMicrophone className="mr-2" />
            {isOpen && 'Text-To-Speech'}
          </h2>
          {isOpen && (
            <label className="block cursor-pointer mt-2">
              <input
                type="checkbox"
                checked={ttsEnabled}
                onChange={() => setTtsEnabled(!ttsEnabled)}
                className="form-checkbox h-4 w-4 text-contrast-orange mr-2"
                style={{ accentColor: 'var(--contrast-orange)' }}
              />
              Enable TTS
            </label>
          )}
        </div>

        {/* API Selection */}
        <div className="mt-4">
          <h2 className="font-bold text-contrast-orange flex items-center">
            <FaCog className="mr-2" />
            {isOpen && 'API Selection'}
          </h2>
          {isOpen && (
            <div className="mt-2">
              {apiOptions.map((api, index) => (
                <label
                  key={api.id}
                  className={`flex items-center cursor-pointer mb-2 ${
                    index === 1 ? 'mb-4' : ''
                  }`}
                >
                  <input
                    type="radio"
                    name="api-service"
                    checked={selectedAPI === api.id}
                    onChange={() => setSelectedAPI(api.id)}
                    className="form-radio h-4 w-4 text-contrast-orange mr-2"
                    style={{ accentColor: 'var(--contrast-orange)' }}
                  />
                  {api.icon && <span className="mr-2">{api.icon}</span>}
                  <span className={api.id === 'o1' ? 'normal-case' : 'capitalize'}>
                    {api.label}
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
