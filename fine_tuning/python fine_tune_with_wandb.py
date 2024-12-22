import os
from dotenv import load_dotenv
from openai import OpenAI
# Load environment variables
load_dotenv()

# Create OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import wandb

# Load environment variables
load_dotenv()

# Retrieve API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
wandb_api_key = os.getenv("WANDB_API_KEY")

# Initialize OpenAI client

# Initialize Weights & Biases
wandb.login(key=wandb_api_key)
wandb.init(project="gpt4o-mini-fine-tune", name="marv-fine-tune", entity="jck411-self")

# File paths for training and validation data
training_file_path = "/home/jack/ayyaihome/fine_tuning/files/marv_fine_tune_train.jsonl"
validation_file_path = "/home/jack/ayyaihome/fine_tuning/files/marv_fine_tune_test.jsonl"

# Upload training and validation files to OpenAI
print("Uploading training and validation files...")
with open(training_file_path, "rb") as train_file:
    training_file = client.files.create(file=train_file, purpose="fine-tune")

with open(validation_file_path, "rb") as valid_file:
    validation_file = client.files.create(file=valid_file, purpose="fine-tune")

print(f"Training File ID: {training_file.id}")
print(f"Validation File ID: {validation_file.id}")

# Start the fine-tuning job with auto parameters
print("Starting fine-tuning job...")
response = client.fine_tuning.jobs.create(model="gpt-4o-mini-2024-07-18",
training_file=training_file.id,
validation_file=validation_file.id,
hyperparameters={
    "batch_size": "auto",
    "learning_rate_multiplier": "auto",
    "n_epochs": "auto"
},
suffix="marv_ft_auto")

print("Fine-tuning job started successfully:")
print(response)

# Log job details to W&B
wandb.log({
    "fine_tuning_job_id": response.id,
    "training_file_id": training_file.id,
    "validation_file_id": validation_file.id,
    "model": "gpt-4o-mini-2024-07-18",
    "hyperparameters": "auto"
})

wandb.finish()
