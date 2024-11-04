"""Application settings and constants."""
import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'
CONFIG_DIR = PROJECT_ROOT / 'config'

# API Settings
MAX_TOKENS = 8000
MAX_CHUNK_SIZE = 128000
MIN_BULLETS_PER_CHUNK = 10
MAX_RETRIES = 7

# Message Processing
ACTION_VERBS = [
    "discussed", "shared", "announced", "implemented", "updated",
    "added", "fixed", "completed", "noted", "mentioned", "explained",
    "developed", "created", "built", "launched", "deployed", "merged",
    "tested", "configured", "optimized", "refactored", "designed",
    "integrated", "released", "improved", "started", "proposed",
    "initiated", "showcased", "demonstrated", "published", "documented",
    "analyzed", "evaluated", "reviewed", "submitted", "prepared",
    "enabled", "established", "introduced", "suggested", "recommended"
]

# Required Environment Variables
REQUIRED_ENV_VARS: Dict[str, str] = {
    "OPENAI_API_KEY": "OpenAI API key",
    "DISCORD_SERVER_ID": "Discord Server ID",
    "TWITTER_CONSUMER_KEY": "Twitter Consumer Key",
    "TWITTER_CONSUMER_SECRET": "Twitter Consumer Secret",
    "TWITTER_ACCESS_TOKEN": "Twitter Access Token",
    "TWITTER_ACCESS_TOKEN_SECRET": "Twitter Access Token Secret",
    "DISCORD_WEBHOOK_URL": "Discord Webhook URL",
    "META_FB_ACCESS_TOKEN": "Meta Facebook Access Token",
    "META_IG_ACCESS_TOKEN": "Meta Instagram Access Token",
    "META_FB_PAGE_ID": "Meta Facebook Page ID",
    "META_IG_ACCOUNT_ID": "Meta Instagram Account ID"
}

def load_env_vars() -> None:
    """Load environment variables from .env file and validate required vars."""
    # Load environment variables from .env file
    env_path = CONFIG_DIR / '.env'
    load_dotenv(env_path)
    
    # Check for required environment variables
    missing_vars = []
    for var_name in REQUIRED_ENV_VARS:
        if not os.getenv(var_name):
            missing_vars.append(f"{var_name} ({REQUIRED_ENV_VARS[var_name]})")
    
    if missing_vars:
        raise ValueError(
            "Missing required environment variables:\n" + 
            "\n".join(f"- {var}" for var in missing_vars)
        )
