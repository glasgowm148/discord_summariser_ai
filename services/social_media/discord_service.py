# services/discord_service.py
import logging
import os
import openai
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from services.http_client import HttpClient

class DiscordService:
    def __init__(self, http_client: HttpClient | None = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.http = http_client or HttpClient()
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
            'Arabic': os.getenv('DISCORD_WEBHOOK_URL_ARABIC'),
            'tester': os.getenv('DISCORD_WEBHOOK_URL_TESTER')
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

    def validate_credentials(self) -> bool:
        """Validate minimum Discord posting configuration."""
        return bool(self.webhook_urls.get('default'))

    def send_message(self, content: str, chunk_size: int = 2000) -> None:
        """Send message to all configured Discord webhooks with translations."""
        if not self.webhook_urls['default']:
            self.logger.error("DISCORD_WEBHOOK_URL is missing")
            return

        for language, url in self.webhook_urls.items():
            if not url:
                self.logger.info("No webhook URL for %s, skipping.", language)
                continue

            if language == 'default':
                processed_content = content
                self.logger.info("Sending original content to Discord")
            else:
                self.logger.info("Translating content to %s", language)
                processed_content = self._translate_content(content, language)

            self._send_chunks_to_webhook(processed_content, url, chunk_size, language)

    def send_reddit_summary(self, content: str, chunk_size: int = 2000) -> None:
        """Send the detailed Reddit summary to the tester webhook."""
        if not self.webhook_urls.get('tester'):
            self.logger.warning("Tester webhook URL not configured, skipping Reddit summary")
            return

        self.logger.info("Sending detailed Reddit summary to tester webhook")
        formatted_content = "```markdown\n" + content + "\n```"
        self._send_chunks_to_webhook(formatted_content, self.webhook_urls['tester'], chunk_size, "reddit")

    def send_daily_message(self, content: str, chunk_size: int = 2000) -> None:
        """Send message to default Discord webhook only (for daily updates)."""
        if not self.webhook_urls['default']:
            self.logger.error("DISCORD_WEBHOOK_URL is missing")
            return

        self.logger.info("Sending daily content to Discord")
        try:
            webhook_url = self.webhook_urls['default']
            self._send_chunks_to_webhook(content, webhook_url, chunk_size, "default")
        except Exception as e:
            self.logger.error("Error sending daily message: %s", e)

    def send_weekly_message(self, content: str, chunk_size: int = 2000) -> None:
        """Send message to default Discord webhook only (for weekly updates)."""
        if not self.webhook_urls['default']:
            self.logger.error("DISCORD_WEBHOOK_URL is missing")
            return

        self.logger.info("Sending weekly content to Discord")
        try:
            webhook_url = self.webhook_urls['default']
            self._send_chunks_to_webhook(content, webhook_url, chunk_size, "default")
        except Exception as e:
            self.logger.error("Error sending weekly message: %s", e)

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
            self.logger.error("Error translating content to %s: %s", language, e)
            return content

    def _send_chunks_to_webhook(self, content: str, webhook_url: str, chunk_size: int, language: str) -> None:
        """Split content into chunks and send to Discord webhook."""
        try:
            if not content:
                self.logger.warning("Empty content provided to _send_chunks_to_webhook")
                return
                
            chunks = self._split_into_chunks(content, chunk_size)
            self.logger.info("Sending %s chunks for %s", len(chunks), language)
            
            for i, chunk in enumerate(chunks):
                try:
                    self.logger.debug("Sending chunk %s/%s (%s chars)", i + 1, len(chunks), len(chunk))
                    response = self.http.post(
                        webhook_url, 
                        json={"content": chunk, "allowed_mentions": {"parse": []}},
                    )
                    
                    if response.status_code == 204:
                        self.logger.info("%s chunk %s/%s sent", language, i + 1, len(chunks))
                        continue
                    raise Exception(f"Discord API returned status code {response.status_code}: {response.text}")
                        
                except Exception as e:
                    self.logger.error("Error sending chunk %s: %s", i + 1, e)
                    raise
                    
        except Exception as e:
            self.logger.error("Error in _send_chunks_to_webhook: %s", e)
            raise

    def _split_into_chunks(self, content: str, chunk_size: int) -> List[str]:
        """Split content into chunks that fit Discord's message size limit."""
        if not content:
            self.logger.warning("Empty content provided to _split_into_chunks")
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
            
        self.logger.debug("Split content into %s chunks", len(chunks))
        return chunks
