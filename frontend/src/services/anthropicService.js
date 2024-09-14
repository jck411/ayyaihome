// Define an asynchronous function to generate an Anthropic AI response
export const generateAnthropicResponse = async (messages, onUpdate) => {
  try {
    const formattedMessages = messages.map(msg => ({
      role: msg.role,
      content: msg.content[0].text
    }));

    const response = await fetch('http://localhost:8000/api/anthropic', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ messages: formattedMessages })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullContent = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const content = decoder.decode(value, { stream: true });
      fullContent += content;
      onUpdate(fullContent, false);
    }

    onUpdate(fullContent, true);
  } catch (error) {
    console.error('Error in generateAnthropicResponse:', error);
    throw error;
  }
};