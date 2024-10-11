import { useCallback } from 'react';

const useScrollToMessage = () => {
  const scrollToAIMessage = useCallback((id) => {
    const element = document.getElementById(`ai-message-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, []);

  return {
    scrollToAIMessage,
  };
};

export default useScrollToMessage;
