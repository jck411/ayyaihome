export const generateAIResponse = async (messages, onUpdate) => {
  try {
    console.log("Sending request to backend with messages:", messages);
    const response = await fetch('http://localhost:5000/api/openai', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ messages })
    });

    console.log('Response status:', response.status);
    if (!response.ok) {
      console.error('Failed to fetch from backend:', response.statusText);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullContent = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const content = decoder.decode(value, { stream: true });
      console.log("Received chunk:", content);
      fullContent += content;
      onUpdate(fullContent);
    }
  } catch (error) {
    console.error('Error calling Python backend:', error);
    throw error;
  }
};
