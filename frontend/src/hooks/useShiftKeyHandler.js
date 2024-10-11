import { useEffect, useCallback } from 'react';

const useShiftKeyHandler = (stopCurrentTTS, isTTSPlaying) => {
  const handleKeyDown = useCallback((event) => {
    if (event.key === "Shift" && isTTSPlaying) {
      stopCurrentTTS();
      console.log('Stopping TTS via Shift key');
    }
  }, [stopCurrentTTS, isTTSPlaying]);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);

    // Cleanup the event listener when the component unmounts
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);
};

export default useShiftKeyHandler;
