# /home/jack/ayyaihome/backend/logging_config.py

import logging
import logging.config
import os
import yaml

def setup_logging(default_level=logging.INFO):
    """Setup logging configuration based on config.yaml"""
    # Determine the path to config.yaml
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')

    # Load config.yaml
    try:
        with open(CONFIG_PATH, 'r') as f:
            config_data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Configuration file not found at {CONFIG_PATH}")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")
        raise

    # Get logging settings
    logging_config = config_data.get('LOGGING', {})
    logging_enabled = logging_config.get('ENABLED', True)
    log_level_str = logging_config.get('LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    if logging_enabled:
        LOGS_DIR = os.path.join(BASE_DIR, 'logs')
        LOG_FILE = os.path.join(LOGS_DIR, 'app.log')

        LOGGING_CONFIG = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S',
                },
                'detailed': {
                    'format': '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] %(name)s: %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S',
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                    'level': log_level,
                    'stream': 'ext://sys.stdout',
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'detailed',
                    'level': log_level,
                    'filename': LOG_FILE,
                    'maxBytes': 10**6,  # 1 MB
                    'backupCount': 5,
                    'encoding': 'utf8',
                },
            },
            'root': {  # Configure the root logger
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': True,
            },
        }

        # Ensure the logs directory exists
        try:
            os.makedirs(LOGS_DIR, exist_ok=True)
        except Exception as e:
            print(f"Failed to create logs directory at {LOGS_DIR}: {e}")
            raise

    else:
        # Disable logging by configuring root logger with no handlers
        LOGGING_CONFIG = {
            'version': 1,
            'disable_existing_loggers': True,  # Disable all existing loggers
            'handlers': {},
            'root': {
                'handlers': [],
                'level': logging.CRITICAL + 10,  # Higher than CRITICAL to suppress all logs
                'propagate': False,
            },
        }

    # Apply the logging configuration
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
    except Exception as e:
        print(f"Failed to apply logging configuration: {e}")
        raise
