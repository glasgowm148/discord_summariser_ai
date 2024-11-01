# services/discord_service.py
import os
import openai
import requests
from pathlib import Path
from typing import List
from dotenv import load_dotenv

class DiscordService:
    def __init__(self):
        # Load environment variables from config/.env
        env_path = Path('config/.env')
        if not env_path.exists():
            raise FileNotFoundError("config/.env file not found. Please copy config/.env.example to config/.env and fill in your values.")
        load_dotenv(env_path)
        
        self.webhook_urls = {
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
        self.language_map = {
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

    def send_message(self, content: str, chunk_size: int = 2000) -> None:
        """Send message to all configured Discord webhooks with translations."""
        if not self.webhook_urls['default']:
            print("Error: 'default' webhook URL is missing. Please set the DISCORD_WEBHOOK_URL environment variable.")
            return

        for language, url in self.webhook_urls.items():
            if not url:
                print(f"No webhook URL for {language}, skipping.")
                continue

            if language == 'default':
                processed_content = content
                print("Sending original content to Discord (default)...")
            else:
                print(f"Translating content to {language}...")
                processed_content = self._translate_content(content, language)

            self._send_chunks_to_webhook(processed_content, url, chunk_size, language)

    def send_daily_message(self, content: str, chunk_size: int = 2000) -> None:
        """Send message to default Discord webhook only (for daily updates)."""
        if not self.webhook_urls['default']:
            print("Error: 'default' webhook URL is missing. Please set the DISCORD_WEBHOOK_URL environment variable.")
            return

        print("Sending daily content to Discord (default webhook only)...")
        try:
            # Print webhook URL for debugging (excluding sensitive parts)
            webhook_url = self.webhook_urls['default']
            if webhook_url:
                safe_url = webhook_url.split('/')
                safe_url[-1] = '****'  # Hide the actual webhook ID
                print(f"Using webhook URL: {'/'.join(safe_url)}")
            
            self._send_chunks_to_webhook(content, webhook_url, chunk_size, "default")
        except Exception as e:
            print(f"Error sending daily message: {str(e)}")
            print(f"Full error details: {type(e).__name__}: {str(e)}")

    def send_weekly_message(self, content: str, chunk_size: int = 2000) -> None:
        """Send message to default Discord webhook only (for weekly updates)."""
        if not self.webhook_urls['default']:
            print("Error: 'default' webhook URL is missing. Please set the DISCORD_WEBHOOK_URL environment variable.")
            return

        print("Sending weekly content to Discord (default webhook only)...")
        try:
            # Print webhook URL for debugging (excluding sensitive parts)
            webhook_url = self.webhook_urls['default']
            if webhook_url:
                safe_url = webhook_url.split('/')
                safe_url[-1] = '****'  # Hide the actual webhook ID
                print(f"Using webhook URL: {'/'.join(safe_url)}")
            
            self._send_chunks_to_webhook(content, webhook_url, chunk_size, "default")
        except Exception as e:
            print(f"Error sending weekly message: {str(e)}")
            print(f"Full error details: {type(e).__name__}: {str(e)}")

    def _translate_content(self, content: str, language: str) -> str:
        """Translate content to specified language using OpenAI."""
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Translate the following content to {self.language_map.get(language, language)}:"},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            return response.model_dump()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error translating content to {language}: {e}")
            return content

    def _send_chunks_to_webhook(self, content: str, webhook_url: str, chunk_size: int, language: str) -> None:
        """Split content into chunks and send to Discord webhook."""
        try:
            if not content:
                print("Warning: Empty content provided to _send_chunks_to_webhook")
                return
                
            chunks = self._split_into_chunks(content, chunk_size)
            print(f"Sending {len(chunks)} chunks for {language}...")
            
            for i, chunk in enumerate(chunks):
                try:
                    # Print chunk details for debugging
                    print(f"\nSending chunk {i + 1}/{len(chunks)} ({len(chunk)} characters)")
                    
                    response = requests.post(
                        webhook_url, 
                        json={"content": chunk, "allowed_mentions": {"parse": []}},
                        timeout=10  # Add timeout
                    )
                    
                    # Print response details
                    print(f"Response status code: {response.status_code}")
                    if response.status_code != 204:
                        print(f"Response text: {response.text}")
                    
                    if response.status_code == 204:
                        print(f"{language} chunk {i + 1}/{len(chunks)} sent successfully.")
                    else:
                        print(f"Failed to send {language} chunk {i + 1}/{len(chunks)}")
                        print(f"Status code: {response.status_code}")
                        print(f"Response: {response.text}")
                        raise Exception(f"Discord API returned status code {response.status_code}: {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"Network error sending chunk {i + 1}: {str(e)}")
                    raise
                    
        except Exception as e:
            print(f"Error in _send_chunks_to_webhook: {str(e)}")
            raise

    def _split_into_chunks(self, content: str, chunk_size: int) -> List[str]:
        """Split content into chunks that fit Discord's message size limit."""
        if not content:
            print("Warning: Empty content provided to _split_into_chunks")
            return []
            
        chunks = []
        current_chunk = ""
        
        for line in content.split("\n"):
            # If the line itself is longer than chunk_size, split it
            if len(line) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    
                # Split long line into multiple chunks
                while line:
                    chunks.append(line[:chunk_size])
                    line = line[chunk_size:]
                continue
                
            # Normal case: add line if it fits
            if len(current_chunk) + len(line) + 1 <= chunk_size:
                current_chunk += line + "\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = line + "\n"
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        print(f"Split content into {len(chunks)} chunks")
        return chunks
