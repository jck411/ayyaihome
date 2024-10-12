import React from 'react';
import { useAppLogic } from './hooks/useAppLogic';
import Layout from './components/Layout';

const App = () => {
  const appLogic = useAppLogic();

  return (
    <Layout appLogic={appLogic} />
  );
};

export default App;
