// Define an asynchronous function to generate an OpenAI or Anthropic response
export const generateAIResponse = async (messages, onUpdate, selectedAPI) => {
  try {
    // Format the messages to include 'role' and 'content' fields
    const formattedMessages = messages.map(msg => {
      // Check if the message is from the Anthropic assistant using metadata and if we are sending to OpenAI
      if (selectedAPI === "openai" && msg.sender === "assistant" && msg.metadata?.assistantType === "anthropic") {
        return {
          role: "user",  // Change role to 'user' for Anthropic assistant messages
          content: `Claude: ${msg.text}`  // Prefix the content with 'Claude:'
        };
      } else {
        return {
          role: msg.sender === "user" ? "user" : "assistant",
          content: msg.text
        };
      }
    });

    console.log("Formatted messages before sending to OpenAI:", formattedMessages); // Debugging log

    // Send the formatted messages to the OpenAI backend
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
