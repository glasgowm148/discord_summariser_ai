"""Application settings and constants."""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'
CONFIG_DIR = PROJECT_ROOT / 'config'

# API Settings
MAX_TOKENS = 8000
MAX_CHUNK_SIZE = 128000
MIN_BULLETS_PER_CHUNK = 5
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
REQUIRED_ENV_VARS = {
    "OPENAI_API_KEY": "OpenAI API key",
    "TWITTER_CONSUMER_KEY": "Twitter Consumer Key",
    "TWITTER_CONSUMER_SECRET": "Twitter Consumer Secret",
    "TWITTER_ACCESS_TOKEN": "Twitter Access Token",
    "TWITTER_ACCESS_TOKEN_SECRET": "Twitter Access Token Secret",
    "DISCORD_WEBHOOK_URL": "Discord Webhook URL"
}
