// hooks/useAppLogic.js
import { useMessageLogic } from '../MessageLogic';
import useAudioPlayer from './useAudioPlayer';
import useWebSocket from './useWebSocket';
import useDarkMode from './useDarkMode';
import useMessagePaneResizer from './useMessagePaneResizer';
import useSidebarState from './useSidebarState';
import useUserInteractionTracker from './useUserInteractionTracker';
import useShiftKeyHandler from './useShiftKeyHandler';
import useScrollToMessage from './useScrollToMessage';

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
  const { stopCurrentTTS, isTTSPlaying } = useAudioPlayer(userInteracted);

  // WebSocket Logic
  const { message, isConnected } = useWebSocket('');

  // Pane Resizer Logic
  const { leftWidth, handleMouseDown } = useMessagePaneResizer();

  // Shift Key Handler
  useShiftKeyHandler(stopCurrentTTS, isTTSPlaying);

  // Scroll to AI Message Logic
  const { scrollToAIMessage } = useScrollToMessage();

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
    isConnected,
    leftWidth,
    handleMouseDown,
    scrollToAIMessage,
    setUserInteracted,
  };
};
