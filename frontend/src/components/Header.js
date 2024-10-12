// src/components/Header.js
import React from 'react';
import StatusBar from './StatusBar';

const Header = (props) => {
  return (
    <header>
      <StatusBar {...props} />
    </header>
  );
};

export default Header;