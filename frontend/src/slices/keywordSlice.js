// src/slices/keywordSlice.js
import { createSlice } from '@reduxjs/toolkit';

const keywordSlice = createSlice({
  name: 'keyword',
  initialState: {
    currentKeyword: null,
    timestamp: null,
  },
  reducers: {
    setKeyword: (state, action) => {
      state.currentKeyword = action.payload.keyword;
      state.timestamp = action.payload.timestamp;
    },
    resetKeyword: (state) => {
      state.currentKeyword = null;
      state.timestamp = null;
    },
  },
});

export const { setKeyword, resetKeyword } = keywordSlice.actions;
export default keywordSlice.reducer;
