import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

def load_environment():
    """Load environment variables from a .env file."""
    load_dotenv()

def load_config() -> dict:
    """Load configuration from the YAML file."""
    CONFIG_PATH = Path(__file__).parent / "config.yaml"
    
    try:
        with open(CONFIG_PATH, 'r') as config_file:
            config_data = yaml.safe_load(config_file)
            return config_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration: {e}")
