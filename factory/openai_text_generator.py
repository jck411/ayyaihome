# openai_text_generator.py

from text_generator_interface import TextGenerator

class OpenAITextGenerator(TextGenerator):
    def __init__(self, client, text_queue, text_generation_complete):
        self.client = client
        self.text_queue = text_queue
        self.text_generation_complete = text_generation_complete

    def generate_text(self):
        import threading

        # Get the prompt from the terminal
        user_prompt = input("Please enter your prompt: ")

        chat_completion = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_prompt}
            ],
            stream=True
        )

        full_response = ""
        for chunk in chat_completion:
            if chunk.choices[0].delta.content:
                new_text = chunk.choices[0].delta.content
                full_response += new_text
                print(new_text, end="", flush=True)  # Print text chunk immediately
                self.text_queue.put(new_text)

        self.text_generation_complete.set()
