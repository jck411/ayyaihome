
# Standard library imports
import json  # Handles JSON data encoding and decoding
import os
import random  # Generates random numbers and makes random selections
import time  # Provides time-related functions
import math  # Offers mathematical functions and constants
from pathlib import Path  # Handles filesystem paths in an object-oriented way
from collections import defaultdict  # Provides a dictionary subclass with default values
import base64  # Provides data encoding and decoding as specified in RFC 3548
import io  # Offers core tools for working with streams
import sys  # Provides access to some variables used or maintained by the interpreter


# Third-party library imports
from dotenv import load_dotenv
import numpy as np  # Supports large, multi-dimensional arrays and matrices
import pandas as pd  # Offers data manipulation and analysis tools
import tiktoken  # Handles tokenization for OpenAI models
from openai import AsyncOpenAI, OpenAI, RateLimitError  # OpenAI API client and related error



# Load environment variables 
load_dotenv()

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))




# Train / Test(validation) Split Function for JSONL Files 80/20 split
def split_jsonl_file(file_path, train_ratio=0.8):
    # Read the input file
    file_path = Path(file_path)
    with file_path.open('r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]
    
    # Shuffle the data
    random.shuffle(data)
    
    # Calculate split index
    split_index = int(len(data) * train_ratio)
    
    # Split the data
    train_data = data[:split_index]
    test_data = data[split_index:]
    
    # Prepare output file paths
    train_file = file_path.with_name(f"{file_path.stem}_train{file_path.suffix}")
    test_file = file_path.with_name(f"{file_path.stem}_test{file_path.suffix}")
    
    # Write train data
    with train_file.open('w', encoding='utf-8') as f:
        for item in train_data:
            json.dump(item, f)
            f.write('\n')
    
    # Write test data
    with test_file.open('w', encoding='utf-8') as f:
        for item in test_data:
            json.dump(item, f)
            f.write('\n')
    
    print(f"Train data saved to: {train_file}")
    print(f"Test data saved to: {test_file}")
    print(f"Train set size: {len(train_data)}")
    print(f"Test set size: {len(test_data)}")
    
    return(train_file, test_file)
# File paths and data processing
file_path = "/home/jack/ayyaihome/fine_tuning/files/marv_fine_tune.jsonl"

# Split the JSONL file into train and test sets
train_test_files = split_jsonl_file(file_path)
print("\n")  # Print a blank line for better output readability

# Convert the returned file paths to strings
train_path, test_path = [str(file) for file in train_test_files]

# Print the paths of the resulting train and test files
print(f"Train file path: {train_path}")
print(f"Test file path: {test_path}")