// /home/jack/ayyaihome/frontend/src/services/openaiService.js

// Define an asynchronous function to generate an OpenAI response
export const generateAIResponse = async (messages, onUpdate, ttsEnabled) => {
  try {
    // Format the messages to include 'role' and 'content' fields
    const formattedMessages = messages.map(msg => {
      if (msg.sender === "user") {
        // Add prefix for the logged-in user based on metadata
        const userPrefix = msg.metadata?.user && msg.metadata.user !== "Guest" ? `${msg.metadata.user}: ` : "";
        return {
          role: "user",  // Role is 'user'
          content: `${userPrefix}${msg.text}`  // Prefix content with user name, or leave as is for Guest
        };
      } else if (msg.sender === "assistant") {
        // Check if the assistant message is from Anthropic, and prepend "Claude:" if so
        const assistantPrefix = msg.metadata?.assistantType === "anthropic" ? "Claude: " : "";
        return {
          role: "assistant",  // Role is 'assistant'
          content: `${assistantPrefix}${msg.text}`  // Prepend "Claude:" if it's from Anthropic
        };
      }
      return msg;  // Return the message as is if it's not from user or assistant
    });

    console.log("Formatted messages before sending to OpenAI:", formattedMessages); // Debugging log

    // Send the formatted messages and TTS state to the OpenAI backend
    const response = await fetch('http://localhost:8000/api/openai', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ messages: formattedMessages, ttsEnabled })  // Include ttsEnabled in the request body
    });

    // Wait until headers are available
    await new Promise((resolve) => setTimeout(resolve, 0));

    const requestId = response.headers.get('X-Request-ID');

    if (!response.ok) {
      throw new Error('Failed to send request to OpenAI backend');
    }

    // Process the streamed response
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullContent = "";

    let isFirstChunk = true;

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        onUpdate(fullContent, true);  // Indicate that the response is complete
        break;
      }
      const content = decoder.decode(value, { stream: true });
      fullContent += content;

      if (isFirstChunk) {
        isFirstChunk = false;
        onUpdate(fullContent, false, requestId);  // Pass requestId on the first update
      } else {
        onUpdate(fullContent);  // Subsequent updates
      }
    }
  } catch (error) {
    console.error('Error in generateAIResponse:', error);
    throw error;
  }
};
