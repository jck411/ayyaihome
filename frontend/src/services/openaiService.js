// Define an asynchronous function to generate an OpenAI response
export const generateAIResponse = async (messages, onUpdate) => {
  try {
    // Format the messages to include 'role' and 'content' fields
    const formattedMessages = messages.map(msg => ({
      role: msg.sender === "user" ? "user" : "assistant",
      content: msg.text
    }));

    // Send the formatted messages to the backend
    const response = await fetch('http://localhost:8000/api/openai', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ messages: formattedMessages })
    });

    if (!response.ok) {
      throw new Error('Failed to send request to OpenAI backend');
    }

    // Process the streamed response
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullContent = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const content = decoder.decode(value, { stream: true });
      fullContent += content;
      onUpdate(fullContent);  // Update content chunk by chunk
    }
  } catch (error) {
    console.error('Error in generateAIResponse:', error);
    throw error;
  }
};
