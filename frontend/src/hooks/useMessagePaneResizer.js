// /hooks/useMessagePaneResizer.js

import { useState, useCallback } from 'react';

const useMessagePaneResizer = () => {
  // State to manage the width of the left pane in the chat area
  const [leftWidth, setLeftWidth] = useState(30);

  // Function to handle dragging the middle cursor to resize the message list panes
  const handleDrag = useCallback((e) => {
    // Calculate the offset for the draggable container
    const containerOffset = (window.innerWidth - 950) / 2;
    // Calculate new width as a percentage of the container's width
    const newLeftWidth = ((e.clientX - containerOffset) / 950) * 100;
    // Set new width if within acceptable bounds (20% to 80%)
    if (newLeftWidth > 20 && newLeftWidth < 80) {
      setLeftWidth(newLeftWidth);
    }
  }, []);

  // Function to handle the end of dragging
  const handleDragEnd = useCallback(() => {
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', handleDragEnd);
  }, [handleDrag]);

  // Function to start the dragging process
  const handleMouseDown = useCallback(() => {
    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', handleDragEnd);
  }, [handleDrag, handleDragEnd]);

  return {
    leftWidth,
    handleMouseDown,
  };
};

export default useMessagePaneResizer;
