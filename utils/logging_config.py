# utils/logging_config.py
import logging
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('summary_generator.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
