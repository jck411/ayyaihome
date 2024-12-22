# Standard library imports
import json
import os
import random
import time
import math
from pathlib import Path
from collections import defaultdict
import base64
import io
import sys

# Third-party library imports
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import tiktoken
from openai import AsyncOpenAI, RateLimitError

# Load environment variables
load_dotenv()

# Create an asynchronous OpenAI client
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define an async function to upload files and create fine-tuning jobs
async def main():
    # Upload the training data to the OpenAI API
    train_set_file = await aclient.files.create(
        file=open("/home/jack/ayyaihome/fine_tuning/files/marv_fine_tune_train.jsonl", "rb"),
        purpose="fine-tune"
    )

    # Upload the test data to the OpenAI API
    test_set_file = await aclient.files.create(
        file=open("/home/jack/ayyaihome/fine_tuning/files/marv_fine_tune_test.jsonl", "rb"),
        purpose="fine-tune"
    )
    
    # Create a fine-tuning job with additional parameters
    all_params_ft_job = await aclient.fine_tuning.jobs.create(
        model="gpt-4o-mini-2024-07-18",
        training_file=train_set_file.id,
        validation_file=test_set_file.id,
        hyperparameters={
            "batch_size": "auto",
            "learning_rate_multiplier": "auto",
            "n_epochs": "auto",
        },
        suffix="marv_ft_0003",
        integrations=None,
        seed=None,
    )

# Run the asynchronous main function
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
