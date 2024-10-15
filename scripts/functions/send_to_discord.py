# send_to_discord.py
import os
import openai
import requests
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

def send_to_discord(content, chunk_size=2000):
    # Retrieve all webhook URLs from environment variables
    webhook_urls = {
        'default': os.getenv('DISCORD_WEBHOOK_URL'),
        'Chinese': os.getenv('DISCORD_WEBHOOK_URL_CHINESE'),
        'Spanish': os.getenv('DISCORD_WEBHOOK_URL_SPANISH'),
        'French': os.getenv('DISCORD_WEBHOOK_URL_FRENCH'),
        'Turkish': os.getenv('DISCORD_WEBHOOK_URL_TURKISH'),
        'Russian': os.getenv('DISCORD_WEBHOOK_URL_RUSSIAN'),
        'Indonesian': os.getenv('DISCORD_WEBHOOK_URL_INDONESIAN'),
        'Italian': os.getenv('DISCORD_WEBHOOK_URL_ITALIAN'),
        'German': os.getenv('DISCORD_WEBHOOK_URL_GERMAN'),
        'Vietnamese': os.getenv('DISCORD_WEBHOOK_URL_VIETNAMESE'),
        'Portuguese': os.getenv('DISCORD_WEBHOOK_URL_PORTUGUESE'),
        'Arabic': os.getenv('DISCORD_WEBHOOK_URL_ARABIC')
    }
    
    if not webhook_urls['default']:
        print("Error: 'default' webhook URL is missing. Please set the DISCORD_WEBHOOK_URL environment variable.")
        return

    # Send original and translated content to respective webhooks
    for language, url in webhook_urls.items():
        if not url:
            print(f"No webhook URL for {language}, skipping.")
            continue

        if language == 'default':
            # Send original content for the default language
            processed_content = content
            print("Sending original content to Discord (default)...")
        else:
            # Translate content for other languages
            print(f"Translating content to {language}...")
            processed_content = translate_content(content, language)

        # Send the content in chunks
        send_chunks_to_webhook(processed_content, url, chunk_size, language)

def translate_content(content, language):
    language_map = {
        "Chinese": "Simplified Chinese",
        "Spanish": "Spanish",
        "French": "French",
        "Turkish": "Turkish",
        "Russian": "Russian",
        "Indonesian": "Indonesian",
        "Italian": "Italian",
        "German": "German",
        "Vietnamese": "Vietnamese",
        "Portuguese": "Portuguese",
        "Arabic": "Arabic"
    }
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": f"Translate the following content to {language_map.get(language, language)}:"},
                      {"role": "user", "content": content}],
            temperature=0.3,
            max_tokens=1500
        )
        return response.model_dump()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error translating content to {language}: {e}")
        return content

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
