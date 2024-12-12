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




def load_and_print_dataset(data_path):
    """
    Load the dataset from a given file path and print initial statistics.
    
    Args:
        data_path (str): Path to the dataset file.
        
    Returns:
        dataset (list): Loaded dataset as a list of dictionaries.
    """
    # Load the dataset
    with open(data_path, 'r', encoding='utf-8') as file:
        dataset = [json.loads(line) for line in file]
    
    # Print initial dataset statistics
    print("Number of examples:", len(dataset))
    print("First example:")
    
    # Print messages from the first example in the dataset
    for message in dataset[0]["messages"]:
        print(message)
    
    return dataset


# Using the function to load and print the dataset
data_path = "/home/jack/ayyaihome/fine_tuning/files/marv_fine_tune.jsonl"
dataset = load_and_print_dataset(data_path)



def check_format_errors(dataset):
    """
    Check for format errors in the dataset and print the results.
    
    Args:
        dataset (list): The dataset to check.
        
    Returns:
        format_errors (dict): A dictionary containing the count of each type of format error.
    """
    # Dictionary to track format errors
    format_errors = defaultdict(int)
    
    # Iterate through each example in the dataset
    for ex in dataset:
        # Check if the example is a dictionary
        if not isinstance(ex, dict):
            format_errors["data_type"] += 1
            continue
        
        # Retrieve the messages list from the example
        messages = ex.get("messages", None)
        if not messages:
            format_errors["missing_messages_list"] += 1
            continue
        
        # Check each message in the messages list
        for message in messages:
            # Check if required keys are present in the message
            if "role" not in message or "content" not in message:
                format_errors["message_missing_key"] += 1
            
            # Check for any unrecognized keys in the message
            if any(k not in ("role", "content", "name", "function_call", "weight") for k in message):
                format_errors["message_unrecognized_key"] += 1
            
            # Validate the role value in the message
            if message.get("role", None) not in ("system", "user", "assistant", "function"):
                format_errors["unrecognized_role"] += 1
            
            # Check content and function_call in the message
            content = message.get("content", None)
            function_call = message.get("function_call", None)
            if (not content and not function_call) or not isinstance(content, str):
                format_errors["missing_content"] += 1
        
        # Ensure at least one message from the assistant is present
        if not any(message.get("role", None) == "assistant" for message in messages):
            format_errors["example_missing_assistant_message"] += 1
    
    # Print the results of the error checks
    if format_errors:
        print("Found possible issues:")
        for key, value in format_errors.items():
            print(f"{key}: {value}")
    else:
        print("No errors found")
    
    return format_errors

format_errors = check_format_errors(dataset)





# Constants
MAX_TOKENS_PER_EXAMPLE = 640 #(max total tokens for openai is 64000 )
TARGET_EPOCHS = 3
MIN_TARGET_EXAMPLES = 10
MAX_TARGET_EXAMPLES = 25000
MIN_DEFAULT_EPOCHS = 1
MAX_DEFAULT_EPOCHS = 25

# Automatically get the encoding for a specific model
encoding = tiktoken.encoding_for_model("gpt-4o")


def process_dataset(dataset, num_tokens_from_messages,
                    num_assistant_tokens_from_messages, token_limit=64000):
    """
    Process the dataset and calculate various statistics.

    Args:
        dataset (list): List of examples in the dataset.
        num_tokens_from_messages (function): Function to count tokens in messages.
        num_assistant_tokens_from_messages (function): Function to count assistant tokens.
        token_limit (int): Maximum token limit for conversations.

    Returns:
        tuple: Contains lists of message counts, conversation lengths, and assistant message lengths.
    """
    n_missing_system = 0
    n_missing_user = 0
    n_messages = []
    convo_lens = []
    assistant_message_lens = []

    for i, ex in enumerate(dataset):
        messages = ex["messages"]
        if not any(message["role"] == "system" for message in messages):
            n_missing_system += 1
        if not any(message["role"] == "user" for message in messages):
            n_missing_user += 1
        n_messages.append(len(messages))
        try:
            convo_lens.append(num_tokens_from_messages(messages))
            assistant_message_lens.append(
                num_assistant_tokens_from_messages(messages)
            )
        except Exception as e:
            print(f"Error processing example {i}:")
            print(f"Messages: {messages}")
            print(f"Error: {str(e)}")
            raise

    n_too_long = sum(l > token_limit for l in convo_lens)

    print_summary(n_missing_system, n_missing_user, n_messages,
                convo_lens, assistant_message_lens, n_too_long, token_limit)
    return n_messages, convo_lens, assistant_message_lens


def print_summary(n_missing_system, n_missing_user, n_messages,
                convo_lens, assistant_message_lens, n_too_long, token_limit):
    """
    Print a summary of the dataset processing results.

    Args:
        n_missing_system (int): Number of examples missing system messages.
        n_missing_user (int): Number of examples missing user messages.
        n_messages (list): List of message counts for each example.
        convo_lens (list): List of conversation lengths in tokens.
        assistant_message_lens (list): List of assistant message lengths in tokens.
        n_too_long (int): Number of conversations exceeding the token limit.
        token_limit (int): Maximum token limit for conversations.
    """
    print("Summary of dataset processing:")
    print(f"Num examples missing system message: {n_missing_system}")
    print(f"Num examples missing user message: {n_missing_user}")
    print(f"Total number of examples: {len(n_messages)}")
    print(f"Average number of messages per example: "
        f"{sum(n_messages) / len(n_messages):.2f}")
    print(f"Average number of total tokens per example: "
        f"{sum(convo_lens) / len(convo_lens):.2f}")
    print(f"Average number of assistant tokens per example: "
        f"{sum(assistant_message_lens) / len(assistant_message_lens):.2f}")
    print(f"{n_too_long} examples may be over the {token_limit} token limit "
        f"and will be truncated during fine-tuning")


def calculate_epochs(n_train_examples):
    """
    Calculate the number of epochs based on the number of training examples.

    Args:
        n_train_examples (int): Number of training examples.

    Returns:
        int: Calculated number of epochs.
    """
    if n_train_examples * TARGET_EPOCHS < MIN_TARGET_EXAMPLES:
        return min(MAX_DEFAULT_EPOCHS,
                math.ceil(MIN_TARGET_EXAMPLES / n_train_examples))
    elif n_train_examples * TARGET_EPOCHS > MAX_TARGET_EXAMPLES:
        return max(MIN_DEFAULT_EPOCHS,
                   MAX_TARGET_EXAMPLES // n_train_examples)
    return TARGET_EPOCHS


def calculate_billing_tokens(convo_lens):
    """
    Calculate the number of billing tokens in the dataset.

    Args:
        convo_lens (list): List of conversation lengths in tokens.

    Returns:
        int: Total number of billing tokens.
    """
    return sum(min(MAX_TOKENS_PER_EXAMPLE, length) for length in convo_lens)


def print_dataset_statistics(n_train_examples, convo_lens):
    """
    Print the dataset statistics and billing information.

    Args:
        n_train_examples (int): Number of training examples.
        convo_lens (list): List of conversation lengths in tokens.
    """
    n_epochs = calculate_epochs(n_train_examples)
    n_billing_tokens = calculate_billing_tokens(convo_lens)

    print(f"Dataset Statistics:")
    print(f"- Number of training examples: {n_train_examples}")
    print(f"- Approximate billable tokens: {n_billing_tokens}")
    print(f"- Default number of epochs: {n_epochs}")
    print(f"- Estimated total billable tokens: {n_epochs * n_billing_tokens}")


def num_tokens_from_messages(messages, tokens_per_message=3, tokens_per_name=1):
    """
    Calculate the number of tokens in a list of messages.

    Args:
        messages (list): List of message dictionaries.
        tokens_per_message (int): Base tokens per message.
        tokens_per_name (int): Additional tokens for the 'name' field.

    Returns:
        int: Total number of tokens.
    """
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if key == "content" and value is None:
                continue
            elif key == "function_call":
                num_tokens += len(encoding.encode(json.dumps(value)))
            else:
                try:
                    num_tokens += len(encoding.encode(str(value)))
                except Exception as e:
                    print(f"Error encoding key: {key}, value: {value}, "
                        f"type: {type(value)}")
                    print(f"Error message: {str(e)}")
                    raise
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # Adding 3 tokens for end of sequence
    return num_tokens


def num_assistant_tokens_from_messages(messages):
    """
    Calculate the number of tokens in assistant messages.

    Args:
        messages (list): List of message dictionaries.

    Returns:
        int: Total number of tokens in assistant messages.
    """
    num_tokens = 0
    for message in messages:
        if message["role"] == "assistant":
            if message.get("content") is not None:
                num_tokens += len(encoding.encode(str(message["content"])))
            if "function_call" in message:
                num_tokens += len(encoding.encode(json.dumps(message["function_call"])))
    return num_tokens


# Process the dataset and extract relevant information
n_messages, convo_lens, assistant_message_lens = process_dataset(
    dataset,
    num_tokens_from_messages,
    num_assistant_tokens_from_messages
)

# Get the total number of examples in the dataset
n_train_examples = len(dataset)

# Print statistics about the dataset
print_dataset_statistics(n_train_examples, convo_lens)