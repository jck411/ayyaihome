export const generateAnthropicResponse = async (messages, onUpdate, selectedAPI, setWebSocket) => {
  return new Promise((resolve, reject) => {
    try {
      const formattedMessages = [];
      let lastRole = null;

      messages.forEach((msg) => {
        let content = msg.text;

        // If the message is from GPT (OpenAI assistant)
        if (msg.sender === "assistant" && msg.metadata?.assistantType === "openai") {
          content = `GPT: ${msg.text}`;
        }

        // Determine the role
        let role = msg.sender === "assistant" && msg.metadata?.assistantType === "anthropic" ? "assistant" : "user";

        // If the last role is the same as the current, concatenate the content
        if (lastRole === role && formattedMessages.length > 0) {
          formattedMessages[formattedMessages.length - 1].content += `\n${content}`;
        } else {
          formattedMessages.push({ role, content });
          lastRole = role;
        }
      });

      console.log("Formatted messages before sending to Anthropic:", formattedMessages);

      const ws = new WebSocket('ws://localhost:8000/ws/anthropic');
      setWebSocket(ws);

      ws.onopen = () => {
        ws.send(JSON.stringify({ messages: formattedMessages }));
      };

      ws.onmessage = (event) => {
        const content = event.data;
        onUpdate(content);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error in generateAnthropicResponse:', error);
        reject(error);
      };

      ws.onclose = () => {
        resolve();
      };

    } catch (error) {
      console.error('Error in generateAnthropicResponse:', error);
      reject(error);
    }
  });
};
