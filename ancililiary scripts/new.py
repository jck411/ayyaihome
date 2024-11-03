

import os

# Define the directory structure
directories = {
    ".": ["main.py", "config.py", "utils.py", "openai_client.py", "tts_processor.py", 
          "audio_player.py", "stream_manager.py", "app_lifecycle.py", "api.py"],
    "tts_services": ["__init__.py", "openai_tts.py"],
    "completion_services": ["__init__.py", "openai_completion.py"],
}

# Create directories and files
for directory, files in directories.items():
    os.makedirs(directory, exist_ok=True)
    for file in files:
        file_path = os.path.join(directory, file)
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                pass  # Create an empty file

print("Directory structure created successfully.")
