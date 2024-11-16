export const generateAIResponse = async (messages, onUpdate) => {
  try {
    // Ensure each message has the correct structure: role and content
    const formattedMessages = messages.map(msg => ({
      role: msg.sender === "user" ? "user" : "assistant",
      content: msg.text
    }));

    console.log("Formatted messages:", formattedMessages);  // Debug log

    // Send the formatted messages to the backend
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ messages: formattedMessages })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response from backend:", errorText);
      throw new Error('Request to Anthropic backend failed');
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
      onUpdate(fullContent);
    }
  } catch (error) {
    console.error('Error in generateAIResponse:', error);
    throw error;
  }
};
