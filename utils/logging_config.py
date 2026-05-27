# utils/logging_config.py
import logging
from datetime import datetime
from pathlib import Path


def get_log_path(filename: str) -> Path:
    """Return dated output log path and create parent directories."""
    log_dir = Path("output") / datetime.utcnow().strftime("%Y-%m-%d") / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / filename

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(get_log_path('summary_generator.log')),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
