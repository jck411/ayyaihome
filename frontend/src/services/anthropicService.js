// Define an asynchronous function to generate an Anthropic AI response
export const generateAnthropicResponse = async (messages, onUpdate) => {
  try {
    // Format the messages, prefix "GPT: " for OpenAI assistant messages based on metadata
    const formattedMessages = messages.map(msg => {
      // Check if the message is from OpenAI assistant and add "GPT: " prefix
      if (msg.sender === "assistant" && msg.metadata?.assistantType === "openai") {
        return {
          role: "assistant",  // Keep the role as "assistant"
          content: `GPT: ${msg.text}`  // Add "GPT:" prefix to the content
        };
      } else {
        // For all other messages, keep the content and role as they are
        return {
          role: msg.sender === "user" ? "user" : "assistant",
          content: msg.text
        };
      }
    });

    console.log("Formatted messages before sending to Anthropic:", formattedMessages);

    // Send the formatted messages to the Anthropic backend
    const response = await fetch('http://localhost:8000/api/anthropic', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ messages: formattedMessages })
    });

    if (!response.ok) {
      throw new Error('Failed to send request to Anthropic backend');
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
    console.error('Error in generateAnthropicResponse:', error);
    throw error;
  }
};
