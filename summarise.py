"""Main entry point for Discord chat summarization."""
import os
import sys
from datetime import datetime
from typing import Optional, Tuple
from dotenv import load_dotenv
from services.reddit_service import RedditService
from pathlib import Path

from config.settings import (
    CONFIG_DIR,
    OUTPUT_DIR,
    REQUIRED_ENV_VARS
)
from services.base_service import BaseService
from services.csv_loader import CsvLoaderService
from services.summary_generator import SummaryGenerator
from services.discord_service import DiscordService
from services.twitter_service import TwitterService
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
            self.discord_service = DiscordService()
            self.twitter_service = TwitterService()
            self.reddit_service = RedditService()
        except Exception as e:
            self.handle_error(e, {"context": "Service initialization"})
            raise

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

    def run(self) -> None:
        """Execute the main summarization process."""
        self.logger.info("Starting execution...")

        try:
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

            print("\nGenerating new summary...")
            summary_result = self._generate_summary()
            if not summary_result:
                self.logger.error("Summary generation failed")
                return

            discord_summary, discord_summary_with_cta, reddit_summary = summary_result
            self._send_to_platforms(discord_summary, discord_summary_with_cta, reddit_summary)

        except Exception as e:
            self.handle_error(e, {"context": "Main execution"})
            raise

    def _generate_summary(self) -> Optional[Tuple[str, str, str]]:
        """Generate summary from latest CSV file."""
        try:
            df, _, _ = self.csv_loader.load_latest_csv(OUTPUT_DIR)
            days_covered = self.csv_loader.get_days_covered()

            self.logger.info("Generating summary...")
            summaries = self.summary_generator.generate_summary(
                df, days_covered
            )

            if not summaries:
                self.logger.error("Summary generation failed")
                return None

            discord_summary, discord_summary_with_cta, reddit_summary = summaries    
            if not discord_summary or not discord_summary_with_cta or not reddit_summary:
                self.logger.error("One or more summaries are missing")
                return None

            self.logger.info(f"Generated Discord Summary:\n{discord_summary}\n")
            self.logger.info(f"Generated Reddit Summary:\n{reddit_summary}\n")
            return discord_summary, discord_summary_with_cta, reddit_summary

        except Exception as e:
            self.handle_error(e, {"context": "Summary generation"})
            return None

    def _send_to_platforms(self, discord_summary: str, discord_summary_with_cta: str, reddit_summary: str) -> None:
        """Send summaries to platforms."""
        try:
            self._send_to_discord(discord_summary)
            if reddit_summary:
                self.discord_service.send_reddit_summary(reddit_summary)
                self._post_to_reddit(reddit_summary)
            self._prompt_twitter_post(discord_summary_with_cta)
        except Exception as e:
            self.handle_error(e, {"context": "Platform distribution"})

    def _send_to_discord(self, summary: str) -> None:
        """Send summary to Discord."""
        try:
            self.logger.info("Sending to Discord...")
            days_covered = self.csv_loader.get_days_covered()

            if days_covered > 5:
                self.logger.info("Sending as weekly message...")
                self.discord_service.send_weekly_message(summary)
            else:
                self.logger.info("Sending as daily message...")
                self.discord_service.send_daily_message(summary)

            self.logger.info("Successfully sent to Discord")

        except Exception as e:
            self.handle_error(e, {
                "context": "Discord message",
                "summary_length": len(summary)
            })

    def _post_to_reddit(self, reddit_summary: str) -> None:
        """Post summary to Reddit if user confirms."""
        try:
            print("\nWould you like to post this summary to Reddit? (yes/no): ")
            if input().strip().lower() == 'yes':
                days = self.csv_loader.get_days_covered()
                title = f"Ergo Development Update - {days} Day Roundup"
                if self.reddit_service.post_to_reddit(title, reddit_summary):
                    self.logger.info("Successfully posted to Reddit")
                else:
                    self.logger.error("Failed to post to Reddit")
        except Exception as e:
            self.handle_error(e, {"context": "Reddit posting"})

    def _prompt_twitter_post(self, summary_with_call_to_action: str) -> None:
        """Prompt user for Twitter posting."""
        try:
            # Format summary for Twitter before asking user
            twitter_summary = self.summary_generator.summary_finalizer.format_for_twitter(
                summary_with_call_to_action)
            print("\nFormatted summary for Twitter:")
            print("-" * 80)
            print(twitter_summary)
            print("-" * 80)

            user_choice = input(
                "\nDo you want to send this summary to Twitter? (yes/no): ").strip().lower()
            if user_choice == 'yes':
                self.twitter_service.send_tweet(twitter_summary)
                self.logger.info("Successfully sent to Twitter")
            else:
                self.logger.info("Summary not sent to Twitter")

        except Exception as e:
            self.handle_error(e, {"context": "Twitter posting"})


if __name__ == "__main__":
    setup_logging()
    summariser = ChatSummariser()
    summariser.run()
