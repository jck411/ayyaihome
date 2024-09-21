// /home/jack/ayyaihome/frontend/src/services/openaiService.js

export const generateAIResponse = async (messages, onUpdate, selectedAPI, setWebSocket) => {
  return new Promise((resolve, reject) => {
    try {
      const formattedMessages = messages.map(msg => {
        if (selectedAPI === "openai" && msg.sender === "assistant" && msg.metadata?.assistantType === "anthropic") {
          return {
            role: "user",
            content: `Claude: ${msg.text}`
          };
        } else {
          return {
            role: msg.sender === "user" ? "user" : "assistant",
            content: msg.text
          };
        }
      });

      console.log("Formatted messages before sending to OpenAI:", formattedMessages);

      const ws = new WebSocket('ws://localhost:8000/ws/openai');
      setWebSocket(ws);  // Set the WebSocket reference

      ws.onopen = () => {
        ws.send(JSON.stringify({ messages: formattedMessages }));
      };

      ws.onmessage = (event) => {
        const content = event.data;
        onUpdate(content);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error in generateAIResponse:', error);
        reject(error);
      };

      ws.onclose = () => {
        resolve();
      };

    } catch (error) {
      console.error('Error in generateAIResponse:', error);
      reject(error);
    }
  });
};
