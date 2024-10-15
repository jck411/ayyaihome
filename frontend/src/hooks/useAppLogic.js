// /home/jack/ayyaihome/frontend/src/hooks/useAppLogic.js

import { useMessageLogic } from '../MessageLogic';
import useAudioPlayer from './useAudioPlayer';
import useWebSocket from './useWebSocket';
import useDarkMode from './useDarkMode';
import useMessagePaneResizer from './useMessagePaneResizer';
import useSidebarState from './useSidebarState';
import useUserInteractionTracker from './useUserInteractionTracker';
import useShiftKeyHandler from './useShiftKeyHandler';
import useScrollToMessage from './useScrollToMessage';
import { useSelector } from 'react-redux';
import { useEffect } from 'react';

export const useAppLogic = () => {
  // Message Logic
  const {
    messages,
    input,
    setInput,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    loggedInUser,
    onLogin,
    ttsEnabled,
    setTtsEnabled,
  } = useMessageLogic();

  // Dark Mode Logic
  const { darkMode, toggleDarkMode } = useDarkMode();

  // Sidebar State Logic
  const { isSidebarOpen, toggleSidebar } = useSidebarState();

  // User Interaction Tracking
  const { userInteracted, setUserInteracted } = useUserInteractionTracker();

  // Audio Player Logic
  const {
    stopCurrentTTS,
    isTTSPlaying,
    isConnected: isAudioConnected,
  } = useAudioPlayer(userInteracted);

  // Keyword Detection WebSocket Logic
  const { message: keywordMessage } = useWebSocket(
    'ws://localhost:8000/ws/keyword'
  );

  // Pane Resizer Logic
  const { leftWidth, handleMouseDown } = useMessagePaneResizer();

  // Shift Key Handler
  useShiftKeyHandler(stopCurrentTTS, isTTSPlaying);

  // Scroll to AI Message Logic
  const { scrollToAIMessage } = useScrollToMessage();

  // Get the keyword from Redux store
  const keyword = useSelector((state) => state.keyword.currentKeyword);

  // Log the keyword only when it changes
  useEffect(() => {
    if (keyword !== null) {
      console.log('Current keyword from Redux:', keyword);
    }
  }, [keyword]);

  // Update selectedAPI based on keyword
  useEffect(() => {
    if (keyword === 'Hey GPT') {
      setSelectedAPI('openai');
      console.log('Selected API set to OpenAI');
    } else if (keyword === 'Hey Claude') {
      setSelectedAPI('anthropic');
      console.log('Selected API set to Anthropic');
    } else if (keyword === 'Hey O1') {
      setSelectedAPI('o1');
      console.log('Selected API set to O1');
    }
    // You can add more conditions for other APIs if needed
  }, [keyword, setSelectedAPI]);

  // Define onMessageClick if not already defined
  const onMessageClick = (messageId) => {
    console.log(`Message ${messageId} clicked`);
    // Implement additional logic as needed, e.g., highlight message, show options, etc.
  };

  return {
    messages,
    input,
    setInput,
    sendMessage,
    selectedAPI,
    setSelectedAPI,
    loggedInUser,
    onLogin,
    ttsEnabled,
    setTtsEnabled,
    darkMode,
    toggleDarkMode,
    isSidebarOpen,
    toggleSidebar,
    stopCurrentTTS,
    isTTSPlaying,
    isAudioConnected,
    leftWidth,
    handleMouseDown,
    scrollToAIMessage,
    setUserInteracted,
    keywordMessage,
    onMessageClick, // Expose onMessageClick
  };
};
