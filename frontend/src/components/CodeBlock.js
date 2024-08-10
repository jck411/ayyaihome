import React, { useState, useEffect } from 'react';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-dark.css'; // A popular dark theme for syntax highlighting

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
    <div className="code-block-container">
      <div className="code-block-header">
        <span>{language.toUpperCase()}</span> {/* Display the language type */}
      </div>
      <pre>
        <code className={`hljs ${language}`}>
          {code}
        </code>
      </pre>
      <CopyToClipboard text={code} onCopy={handleCopy}>
        <button className="copy-code-button">
          {isCopied ? 'Copied' : 'Copy'}
        </button>
      </CopyToClipboard>
    </div>
  );
};

export default CodeBlock;
