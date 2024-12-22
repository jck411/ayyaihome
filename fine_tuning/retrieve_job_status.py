import os
import time
from openai import OpenAI
import wandb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
wandb_api_key = os.getenv("WANDB_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# Initialize W&B
wandb.login(key=wandb_api_key)
wandb.init(project="gpt4o-mini-fine-tune", name="marv-fine-tune", entity="jck411-self")

# File paths
training_file_path = "/home/jack/ayyaihome/fine_tuning/files/marv_fine_tune_train.jsonl"
validation_file_path = "/home/jack/ayyaihome/fine_tuning/files/marv_fine_tune_test.jsonl"

# Step 1: Upload Training and Validation Files
print("Uploading training and validation files...")
training_file = client.files.create(file=open(training_file_path, "rb"), purpose="fine-tune")
validation_file = client.files.create(file=open(validation_file_path, "rb"), purpose="fine-tune")

print(f"Training File ID: {training_file.id}")
print(f"Validation File ID: {validation_file.id}")

# Log file IDs to W&B
wandb.log({
    "training_file_id": training_file.id,
    "validation_file_id": validation_file.id
})

# Step 2: Start Fine-Tuning Job
print("Starting fine-tuning job...")
response = client.fine_tuning.jobs.create(
    model="gpt-4o-mini-2024-07-18",
    training_file=training_file.id,
    validation_file=validation_file.id,
    hyperparameters={
        "batch_size": "auto",
        "learning_rate_multiplier": "auto",
        "n_epochs": "auto"
    },
    suffix="marv_ft_auto"
)

job_id = response.id
print(f"Fine-tuning job started: {job_id}")
wandb.log({"fine_tuning_job_id": job_id})

# Step 3: Poll Job Status Until Completion
start_time = time.time()

while True:
    job_status = client.fine_tuning.jobs.retrieve(job_id)
    status = job_status.status
    elapsed_time = (time.time() - start_time) / 60  # Elapsed time in minutes

    # Log status and elapsed time to W&B
    wandb.log({
        "job_status": status,
        "elapsed_time_minutes": elapsed_time
    })

    print(f"Job Status: {status}, Elapsed Time: {elapsed_time:.2f} minutes")

    if status in ["succeeded", "failed", "cancelled"]:
        print(f"Fine-tuning job complete: {status}")
        break

    time.sleep(30)  # Poll every 30 seconds

# Step 4: Fetch Final Results and Log to W&B
final_status = client.fine_tuning.jobs.retrieve(job_id)
fine_tuned_model = final_status.fine_tuned_model
result_files = final_status.result_files

print(f"Final Status: {final_status.status}")
print(f"Fine-Tuned Model: {fine_tuned_model}")
print(f"Result Files: {result_files}")

# Log final results to W&B
wandb.log({
    "final_status": final_status.status,
    "fine_tuned_model": fine_tuned_model,
    "result_files": result_files
})

# Finish W&B Run
wandb.finish()
print("W&B logging complete.")
