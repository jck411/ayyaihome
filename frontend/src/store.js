// src/store.js

import { configureStore } from '@reduxjs/toolkit';
import keywordReducer from './slices/keywordSlice'; // We'll create this slice in the next step

const store = configureStore({
  reducer: {
    keyword: keywordReducer,
    // Add other reducers here if needed
  },
});

export default store;
