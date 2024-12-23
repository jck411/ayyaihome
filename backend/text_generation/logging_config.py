# /home/jack/ayyaihome/backend/text_generation/logging_config.py

import logging

# ==========================
# Logging Configuration
# ==========================
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG to capture all levels of logs
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()  # Logs will be output to the terminal
    ]
)

logger = logging.getLogger(__name__)
