"""Main entry point for Discord chat summarization."""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from config.settings import (
    CONFIG_DIR,
    OUTPUT_DIR,
    REQUIRED_ENV_VARS
)
from services.base_service import BaseService
from services.csv_loader import CsvLoaderService
from services.summary_generator import SummaryGenerator
from helpers.processors.bullet_processor import BulletPoint
from utils.logging_config import setup_logging


class ChatSummariser(BaseService):
    def __init__(self):
        super().__init__()
        self.initialize()

    def initialize(self) -> None:
        """Initialize environment and services."""
        try:
            self._load_environment()
            self._validate_environment()
            self._initialize_services()
        except Exception as e:
            self.handle_error(e, {"context": "Initialization"})
            raise

    def _load_environment(self) -> None:
        """Load environment variables."""
        env_path = CONFIG_DIR / '.env'
        if not env_path.exists():
            raise FileNotFoundError(
                "config/.env file not found. Please copy config/.env.example "
                "to config/.env and fill in your values."
            )
        load_dotenv(env_path)

    def _validate_environment(self) -> None:
        """Validate required environment variables."""
        missing_vars = [
            desc for var, desc in REQUIRED_ENV_VARS.items()
            if not os.getenv(var)
        ]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}")

        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url and not webhook_url.startswith('https://discord.com/api/webhooks/'):
            raise ValueError(
                "DISCORD_WEBHOOK_URL must start with 'https://discord.com/api/webhooks/'")

    def _initialize_services(self) -> None:
        """Initialize required services."""
        try:
            self.csv_loader = CsvLoaderService()
            self.summary_generator = SummaryGenerator(
                os.getenv("OPENAI_API_KEY"))
            self.discord_service = None
            self.twitter_service = None
            self.reddit_service = None
            self.meta_service = None
        except Exception as e:
            self.handle_error(e, {"context": "Service initialization"})
            raise

    # Rest of the code remains the same as in the previous version
    def get_latest_summary(self) -> Optional[str]:
        """Get the latest summary from output/sent_summaries.md."""
        try:
            summaries_file = Path(OUTPUT_DIR) / 'sent_summaries.md'
            if summaries_file.exists():
                content = summaries_file.read_text().strip()
                if content:
                    # Split by markdown headers and get all entries
                    summaries = content.split('\n## ')
                    if len(summaries) > 1:
                        # Filter for Discord summaries and get the latest one
                        discord_summaries = [s for s in summaries if 'Discord Summary' in s.split('\n')[0]]
                        if discord_summaries:
                            latest = '## ' + discord_summaries[-1]
                            # Extract the actual summary content (remove the header)
                            summary_lines = latest.split('\n')[2:]  # Skip header and empty line
                            return '\n'.join(summary_lines)
        except Exception as e:
            self.handle_error(e, {"context": "Reading latest summary"})
        return None

    async def run(self) -> None:
        """Execute the main summarization process."""
        self.logger.info("Starting execution...")

        try:
            # Load the data once
            df, _, days_covered = self.csv_loader.load_latest_csv(OUTPUT_DIR)

            # Check for latest summary
            latest_summary = self.get_latest_summary()
            if latest_summary:
                print("\nLatest summary found:")
                print("-" * 50)
                print(latest_summary)
                print("-" * 50)
                choice = input("\nWould you like to use this summary instead of generating a new one? (y/n): ").lower()
                if choice == 'y':
                    print("\nUsing existing summary. Done!")
                    return

            # Generate bullets first
            print("\nGenerating initial summary bullets...")
            discord_summary, discord_summary_with_cta, reddit_summary = self.summary_generator.generate_summary(df, days_covered)
            
            if not discord_summary or not reddit_summary:
                self.logger.error("Failed to generate initial summary")
                return

            # Store the generated bullets for reuse
            generated_bullets = self.summary_generator.bullet_processor.get_last_processed_bullets()

            # Confirm bullet generation
            print("\nGenerated Summary Bullets:")
            print("-" * 50)
            for bullet in generated_bullets:
                print(bullet.content)
            print("-" * 50)

            # Discord Summary
            if input("\nWould you like to generate a Discord summary from these bullets? (y/n): ").lower() == 'y':
                print("\nDiscord Summary:")
                print("-" * 50)
                print(discord_summary)
                print("-" * 50)
                if input("\nWould you like to send this summary to Discord? (y/n): ").lower() == 'y':
                    self._send_to_discord(discord_summary)

            # Reddit Summary
            if input("\nWould you like to generate a Reddit summary from these bullets? (y/n): ").lower() == 'y':
                print("\nReddit Summary:")
                print("-" * 50)
                print(reddit_summary)
                print("-" * 50)
                if input("\nWould you like to post this summary to Reddit? (y/n): ").lower() == 'y':
                    self._get_discord_service().send_reddit_summary(reddit_summary)
                    await self._post_to_reddit(reddit_summary)

            # Twitter Summary
            if input("\nWould you like to generate a Twitter summary from these bullets? (y/n): ").lower() == 'y':
                # Convert bullet points to their string content
                bullet_strings = [bullet.content for bullet in generated_bullets]
                
                # Generate Twitter summary
                twitter_summary, twitter_summary_with_cta, _ = self.summary_generator.summary_finalizer.create_final_summary(
                    bullet_strings, days_covered
                )
                
                if twitter_summary:
                    formatted_summary = self.summary_generator.summary_finalizer.format_for_social_media(
                        twitter_summary_with_cta, 'twitter'
                    )
                    print("\nFormatted Twitter summary:")
                    print("-" * 50)
                    print(formatted_summary)
                    print("-" * 50)
                    if input("\nWould you like to post this summary to Twitter? (y/n): ").lower() == 'y':
                        self._get_twitter_service().send_tweet(formatted_summary)
                        self.logger.info("Successfully sent to Twitter")
                else:
                    self.logger.error("Twitter summary generation failed")

            # Meta Summary
            if input("\nWould you like to generate a Meta platforms summary from these bullets? (y/n): ").lower() == 'y':
                # Convert bullet points to their string content
                bullet_strings = [bullet.content for bullet in generated_bullets]
                
                # Generate Meta summary
                meta_summary, meta_summary_with_cta, _ = self.summary_generator.summary_finalizer.create_final_summary(
                    bullet_strings, days_covered
                )
                
                if meta_summary:
                    # Meta service handles its own preview and confirmation
                    await self._prompt_meta_post(meta_summary_with_cta)
                else:
                    self.logger.error("Meta summary generation failed")

        except Exception as e:
            self.handle_error(e, {"context": "Main execution"})
            raise

    def _send_to_discord(self, summary: str) -> None:
        """Send summary to Discord."""
        try:
            self.logger.info("Sending to Discord...")
            days_covered = self.csv_loader.get_days_covered()

            if days_covered > 5:
                self.logger.info("Sending as weekly message...")
                self._get_discord_service().send_weekly_message(summary)
            else:
                self.logger.info("Sending as daily message...")
                self._get_discord_service().send_daily_message(summary)

            self.logger.info("Successfully sent to Discord")

        except Exception as e:
            self.handle_error(e, {
                "context": "Discord message",
                "summary_length": len(summary)
            })

    async def _post_to_reddit(self, reddit_summary: str) -> None:
        """Post summary to Reddit."""
        try:
            days = self.csv_loader.get_days_covered()
            title = f"Ergo Development Update - {days} Day Roundup"
            if await self._get_reddit_service().post_to_reddit(title, reddit_summary):
                self.logger.info("Successfully posted to Reddit")
            else:
                self.logger.error("Failed to post to Reddit")
        except Exception as e:
            self.handle_error(e, {"context": "Reddit posting"})

    async def _prompt_meta_post(self, summary_with_call_to_action: str) -> None:
        """Prompt user for Meta platform posting."""
        try:
            await self._get_meta_service().prompt_and_post(summary_with_call_to_action)
            self.logger.info("Meta platform posting process completed")
        except Exception as e:
            self.handle_error(e, {"context": "Meta posting"})

    def _get_discord_service(self):
        """Create Discord service only when posting is requested."""
        if self.discord_service is None:
            from services.social_media.discord_service import DiscordService
            self.discord_service = DiscordService()
        return self.discord_service

    def _get_twitter_service(self):
        """Create Twitter service only when posting is requested."""
        if self.twitter_service is None:
            from services.social_media.twitter_service import TwitterService
            self.twitter_service = TwitterService()
        return self.twitter_service

    def _get_reddit_service(self):
        """Create Reddit service only when posting is requested."""
        if self.reddit_service is None:
            from services.social_media.reddit_service import RedditService
            self.reddit_service = RedditService()
        return self.reddit_service

    def _get_meta_service(self):
        """Create Meta service only when posting is requested."""
        if self.meta_service is None:
            from services.meta_service import MetaService
            self.meta_service = MetaService()
        return self.meta_service


if __name__ == "__main__":
    setup_logging()
    summariser = ChatSummariser()
    asyncio.run(summariser.run())
