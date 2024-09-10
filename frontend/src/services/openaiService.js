// Define an asynchronous function to generate an OpenAI response
export const generateAIResponse = async (messages, onUpdate) => {
  try {
    const response = await fetch('http://localhost:8000/api/openai', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ messages })
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
