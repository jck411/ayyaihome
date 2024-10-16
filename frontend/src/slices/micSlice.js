// src/slices/micSlice.js

import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  isListening: false,
  isTTSPlaying: false,
  lastActivityTime: null, // Timestamp of the last activity
};

const micSlice = createSlice({
  name: 'mic',
  initialState,
  reducers: {
    setIsListening(state, action) {
      state.isListening = action.payload;
    },
    setIsTTSPlaying(state, action) {
      state.isTTSPlaying = action.payload;
    },
    updateLastActivityTime(state) {
      state.lastActivityTime = Date.now();
    },
  },
});

export const { setIsListening, setIsTTSPlaying, updateLastActivityTime } = micSlice.actions;
export default micSlice.reducer;
