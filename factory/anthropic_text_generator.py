# anthropic_text_generator.py

from text_generator_interface import TextGenerator

class AnthropicTextGenerator(TextGenerator):
    def __init__(self, client, text_queue, text_generation_complete):
        self.client = client
        self.text_queue = text_queue
        self.text_generation_complete = text_generation_complete

    def generate_text(self):
        import threading
        import anthropic

        # Get the prompt from the terminal
        user_prompt = input("Please enter your prompt: ")

        # Prepare the messages
        messages = [{"role": "user", "content": user_prompt}]

        # Start streaming response from Claude
        with self.client.messages.stream(
            max_tokens=1024,
            messages=messages,
            model="claude-3-5-sonnet-20241022",
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                self.text_queue.put(text)

        self.text_generation_complete.set()
