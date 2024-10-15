import { createSlice } from '@reduxjs/toolkit';

const keywordSlice = createSlice({
  name: 'keyword',
  initialState: {
    currentKeyword: null,
    timestamp: null,
    isConnected: false, // Add isConnected to the initial state
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
    setKeywordConnectionStatus: (state, action) => {
      state.isConnected = action.payload; // Update the connection status
    },
  },
});

export const { setKeyword, resetKeyword, setKeywordConnectionStatus } = keywordSlice.actions;
export default keywordSlice.reducer;
