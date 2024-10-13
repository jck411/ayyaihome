// src/components/KeywordListener.js

import { useEffect } from "react";

const KeywordListener = ({ keywordMessage }) => {
  useEffect(() => {
    if (keywordMessage) {
      console.log("Keyword detected:", keywordMessage);
      alert("Keyword detected: " + keywordMessage);  // Optional: show alert when keyword is detected
    }
  }, [keywordMessage]);

  return null; // No UI rendering needed
};

export default KeywordListener;
