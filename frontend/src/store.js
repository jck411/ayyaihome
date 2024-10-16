// src/store.js

import { configureStore } from '@reduxjs/toolkit';
import keywordReducer from './slices/keywordSlice';
import micReducer from './slices/micSlice'; // Import the new micSlice

const store = configureStore({
  reducer: {
    keyword: keywordReducer,
    mic: micReducer, // Add micReducer to the store
    // Add other reducers here if needed
  },
});

export default store;
