import { useState, useCallback } from 'react';

const useSidebarState = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = useCallback(() => setSidebarOpen(prev => !prev), []);

  return {
    isSidebarOpen,
    toggleSidebar,
  };
};

export default useSidebarState;
