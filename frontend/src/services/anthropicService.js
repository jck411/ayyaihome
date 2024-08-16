// Define an asynchronous function to generate a response from the Anthropic API
// 'messages' is the input to be sent to the backend
// 'onUpdate' is a callback function that will be called with the updated content
export const generateAnthropicResponse = async (messages, onUpdate) => {
  try {
    // Ensure messages are in the correct format
    const formattedMessages = messages.map(msg => ({
      role: msg.sender === "user" ? "user" : "assistant",
      content: msg.text
    }));

    // Make a POST request to the backend API
    const response = await fetch('http://localhost:8000/api/anthropic', {
      method: 'POST',  // Use the POST method
      headers: {
        'Content-Type': 'application/json'  // Set the content type to JSON
      },
      body: JSON.stringify({ 
        model: "claude-3-5-sonnet-20240620",  // Specify the correct model as required by Anthropic
        messages: formattedMessages // Include the messages array as per Anthropic's API documentation
      })
    });

    // Check if the response is not OK (status code 200-299)
    if (!response.ok) {
      console.error('Failed to fetch response from server', response.statusText);
      return;  // Exit the function if the request failed
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
    // Log the error and rethrow it
    console.error('Error fetching data:', error);
    throw error;
  }
};
