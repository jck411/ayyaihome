// services/openaiService.js

// Define an asynchronous function to generate an AI response
// 'messages' is the input to be sent to the backend
// 'onUpdate' is a callback function that will be called with the updated content
export const generateAIResponse = async (messages, onUpdate) => {
  try {
    // Make a POST request to the backend API
    const response = await fetch('http://localhost:8000/api/chat', {  // Changed endpoint
      method: 'POST',  // Use the POST method
      headers: {
        'Content-Type': 'application/json',  // Set the content type to JSON
      },
      body: JSON.stringify({ messages }),  // Convert the messages to a JSON string for the request body
    });

    // Check if the response is not OK (status code 200-299)
    if (!response.ok) {
      throw new Error("Failed to fetch AI response");
    }

    // Create a reader to read the response body as a stream
    const reader = response.body.getReader();
    // Create a TextDecoder to decode the streamed text
    const decoder = new TextDecoder('utf-8');
    // Initialize a variable to hold the full content received
    let fullContent = "";

    // Continuously read from the stream until done
    while (true) {
      // Read a chunk from the response body
      const { done, value } = await reader.read();
      if (done) break;  // Exit the loop if the reading is done
      // Decode the chunk of data
      const content = decoder.decode(value, { stream: true });
      // Append the chunk to the full content
      fullContent += content;
      // Call the onUpdate callback with the full content so far
      onUpdate(fullContent);
    }
  } catch (error) {
    // Log the error and rethrow it to be handled by the caller
    console.error("Error in generating AI response:", error);
    throw error;
  }
};
