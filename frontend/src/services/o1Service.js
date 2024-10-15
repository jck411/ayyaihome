// /home/jack/ayyaihome/frontend/src/services/o1Service.js

// Define an asynchronous function to generate a response from the O1 model
export const generateO1Response = async (messages, onUpdate) => {
    try {
      // Format the messages to include 'role' and 'content' fields
      const formattedMessages = messages.map((msg) => {
        if (msg.sender === "user") {
          // Add prefix for the logged-in user based on metadata
          const userPrefix =
            msg.metadata?.user && msg.metadata.user !== "Guest"
              ? `${msg.metadata.user}: `
              : "";
          return {
            role: "user", // Role is 'user'
            content: `${userPrefix}${msg.text}`, // Prefix content with user name, or leave as is for Guest
          };
        } else if (msg.sender === "assistant") {
          // Handle assistant messages
          return {
            role: "assistant", // Role is 'assistant'
            content: msg.text, // Use the assistant's text as is
          };
        }
        return msg; // Return the message as is if it's not from user or assistant
      });
  
      console.log("Formatted messages before sending to O1 model:", formattedMessages);
  
      // Send the formatted messages to the O1 backend
      const response = await fetch("http://localhost:8000/api/o1", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages: formattedMessages }),
      });
  
      if (!response.ok) {
        throw new Error("Failed to send request to O1 backend");
      }
  
      // Process the streamed response
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let fullContent = "";
  
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          onUpdate(fullContent, true); // Indicate that the response is complete
          break;
        }
        const content = decoder.decode(value, { stream: true });
        fullContent += content;
        onUpdate(fullContent);
      }
    } catch (error) {
      console.error("Error in generateO1Response:", error);
      throw error;
    }
  };
  