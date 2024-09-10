// Define an asynchronous function to generate an Anthropic AI response
export const generateAnthropicResponse = async (messages, onUpdate) => {
  try {
    const formattedMessages = messages.map(msg => ({
      role: msg.sender === "user" ? "user" : "assistant",  // Ensure correct roles
      content: msg.text
    }));

    const response = await fetch('http://localhost:8000/api/anthropic', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ messages: formattedMessages })
    });

    if (!response.ok) {
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullContent = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const content = decoder.decode(value, { stream: true });
      fullContent += content;
      onUpdate(fullContent);
    }
  } catch (error) {
    throw error;
  }
};
