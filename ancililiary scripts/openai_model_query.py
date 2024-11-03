from openai import OpenAI
from dotenv import load_dotenv
import os

def list_models_sorted(api_key):
    # Instantiate the OpenAI client with the provided API key
    client = OpenAI(api_key=api_key)

    # List all available models
    models = client.models.list()

    # Sort models by id in reverse order (newest first)
    sorted_models = sorted(models, key=lambda model: model.id, reverse=True)
    
    return sorted_models

def main():
    # Load environment variables from the .env file
    load_dotenv()

    # Retrieve the OpenAI API key from the environment
    api_key = os.getenv('OPENAI_API_KEY')

    # List all available models using the API key and sort them
    models = list_models_sorted(api_key)

    # Iterate over the sorted models and print the model IDs
    for model in models:
        print(model.id)

if __name__ == "__main__":
    main()
