// /home/jack/ayyaihome/frontend/src/services/chatService.js

export const generateChatResponse = async (messages, selectedAPI, onUpdate, setWebSocket) => {
  return new Promise((resolve, reject) => {
    try {
      const formattedMessages = [];
      let lastRole = null;

      messages.forEach((msg) => {
        let content = msg.text;

        // Adjust content based on assistant type
        if (msg.sender === "assistant") {
          if (msg.metadata?.assistantType === "openai" && selectedAPI === "anthropic") {
            content = `GPT: ${msg.text}`;
          } else if (msg.metadata?.assistantType === "anthropic" && selectedAPI === "openai") {
            content = `Claude: ${msg.text}`;
          }
        }

        // Determine the role
        let role = msg.sender === "assistant" && msg.metadata?.assistantType === selectedAPI ? "assistant" : "user";

        // Concatenate messages with the same role
        if (lastRole === role && formattedMessages.length > 0) {
          formattedMessages[formattedMessages.length - 1].content += `\n${content}`;
        } else {
          formattedMessages.push({ role, content });
          lastRole = role;
        }
      });

      console.log("Formatted messages before sending to chat:", formattedMessages);

      const ws = new WebSocket('ws://localhost:8000/ws/chat');
      setWebSocket(ws);

      ws.onopen = () => {
        // Send the initial message to specify the API type
        ws.send(JSON.stringify({ api: selectedAPI }));
        // Then send the actual messages
        ws.send(JSON.stringify({ messages: formattedMessages }));
      };

      ws.onmessage = (event) => {
        const content = event.data; // Treat as plain text
        onUpdate(content); // Pass the plain text to the update function
      };

      ws.onerror = (error) => {
        console.error('WebSocket error in generateChatResponse:', error);
        reject(new Error('WebSocket connection error.'));
      };

      ws.onclose = () => {
        resolve();
      };
    } catch (error) {
      console.error('Error in generateChatResponse:', error);
      reject(error);
    }
  });
};
