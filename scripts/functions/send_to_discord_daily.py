# send_to_discord_daily.py
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

def send_to_discord_daily(content, chunk_size=2000):
    default_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

    if not default_webhook_url:
        print("Error: 'default' webhook URL is missing. Please set the DISCORD_WEBHOOK_URL environment variable.")
        return

    print("Sending daily content to Discord (default webhook only)...")
    send_chunks_to_webhook(content, default_webhook_url, chunk_size, "default")

def send_chunks_to_webhook(content, webhook_url, chunk_size, language):
    chunks = split_into_chunks(content, chunk_size)
    for i, chunk in enumerate(chunks):
        response = requests.post(webhook_url, json={"content": chunk, "allowed_mentions": {"parse": []}})
        if response.status_code == 204:
            print(f"{language} chunk {i + 1} sent successfully.")
        else:
            print(f"Failed to send {language} chunk {i + 1}: {response.status_code}")

def split_into_chunks(content, chunk_size):
    chunks = []
    current_chunk = ""
    for line in content.split("\n"):
        if len(current_chunk) + len(line) + 1 <= chunk_size:
            current_chunk += line + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks
