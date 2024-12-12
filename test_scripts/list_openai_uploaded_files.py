from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables (if you're storing your API key in a .env file)
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# List uploaded files
response = client.files.list()

# Check if there are any files uploaded
if not response.data:
    print("No files found.")
    exit()

# Display the list of files
print("Uploaded Files:")
# Use dot notation to access attributes
files = {file.filename: file.id for file in response.data}  # Map filenames to IDs
for filename, file_id in files.items():
    print(f"Name: {filename}, ID: {file_id}")

# Ask if the user wants to delete one or all files
action = input("\nDo you want to delete a specific file or all files? (Enter 'one' or 'all'): ").strip().lower()

if action == "one":
    # Prompt the user to select a file by name
    file_name = input("\nEnter the name of the file you want to delete: ").strip()

    try:
        file_id = files.get(file_name)
        if not file_id:
            print("\nError: File not found. Make sure you entered the correct file name.")
            exit()

        # Delete the selected file
        client.files.delete(file_id)
        print(f"\nFile '{file_name}' has been deleted successfully.")
    except Exception as e:
        print(f"\nError: {e}")

elif action == "all":
    # Confirm before deleting all files
    confirmation = input("\nAre you sure you want to delete all files? (yes/no): ").strip().lower()
    if confirmation == "yes":
        try:
            for file_name, file_id in files.items():
                client.files.delete(file_id)
                print(f"File '{file_name}' deleted.")
            print("\nAll files have been deleted successfully.")
        except Exception as e:
            print(f"\nError: {e}")
    else:
        print("\nDeletion of all files canceled.")

else:
    print("\nInvalid option. Please restart the script and choose 'one' or 'all'.")
