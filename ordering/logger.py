import os
import logging
from datetime import datetime

def get_logger(name: str = "default_logger", log_dir: str = "logs"):
    # Create logs directory
    os.makedirs(log_dir, exist_ok=True)

    # Unique file name with timestamp
    file_name = f"{name,datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
    log_file_path = os.path.join(log_dir, file_name)

    # Create a custom logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers on multiple calls
    if not logger.handlers:
        # File Handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    return logger
