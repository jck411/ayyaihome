import React, { useState, useEffect } from 'react';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css'; // Using a dark theme

const CodeBlock = ({ code, language }) => {
  const [isCopied, setIsCopied] = useState(false);

  useEffect(() => {
    hljs.highlightAll();
  }, []);

  const handleCopy = () => {
    setIsCopied(true);
    setTimeout(() => {
      setIsCopied(false);
    }, 2000);
  };

  return (
    <div className="relative bg-dark-bg text-dark-text p-4 rounded-lg">
      <pre>
        <code className={`hljs ${language}`}>
          {code}
        </code>
      </pre>
      <CopyToClipboard text={code} onCopy={handleCopy}>
        <button className="absolute top-2 right-2 bg-gray-700 p-1 rounded text-xs hover:bg-gray-600">
          {isCopied ? 'Copied' : 'Copy'}
        </button>
      </CopyToClipboard>
      <div className="text-xs text-gray-400 absolute bottom-2 right-2">{language}</div>
    </div>
  );
};

export default CodeBlock;
