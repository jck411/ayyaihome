import { useState, useEffect } from 'react';

const useUserInteractionTracker = () => {
  const [userInteracted, setUserInteracted] = useState(false);

  useEffect(() => {
    const handleUserInteraction = () => {
      setUserInteracted(true);
      window.removeEventListener('click', handleUserInteraction);
      window.removeEventListener('keydown', handleUserInteraction);
    };

    // Add event listeners for user interaction
    window.addEventListener('click', handleUserInteraction);
    window.addEventListener('keydown', handleUserInteraction);

    // Cleanup the event listeners
    return () => {
      window.removeEventListener('click', handleUserInteraction);
      window.removeEventListener('keydown', handleUserInteraction);
    };
  }, []);

  return {
    userInteracted,
    setUserInteracted, // Expose setUserInteracted so it can be used in App.js
  };
};

export default useUserInteractionTracker;
