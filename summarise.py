"""Main entry point for Discord chat summarization."""
import os
from typing import Optional, Tuple
from dotenv import load_dotenv

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
        except Exception as e:
            self.handle_error(e, {"context": "Service initialization"})
            raise

    def run(self) -> None:
        """Execute the main summarization process."""
        self.logger.info("Starting execution...")

        try:
            summary_result = self._generate_summary()
            if not summary_result:
                self.logger.error("Summary generation failed")
                return

            summary, summary_with_call_to_action = summary_result
            self._send_to_platforms(summary, summary_with_call_to_action)

        except Exception as e:
            self.handle_error(e, {"context": "Main execution"})
            raise

    def _generate_summary(self) -> Optional[Tuple[str, str]]:
        """Generate summary from latest CSV file."""
        try:
            df, _, _ = self.csv_loader.load_latest_csv(OUTPUT_DIR)
            days_covered = self.csv_loader.get_days_covered()

            self.logger.info("Generating summary...")
            summary, summary_with_call_to_action = self.summary_generator.generate_summary(
                df, days_covered
            )

            if not summary:
                self.logger.error("Summary generation failed")
                return None

            self.logger.info(f"Generated Summary:\n{summary}\n")
            return summary, summary_with_call_to_action

        except Exception as e:
            self.handle_error(e, {"context": "Summary generation"})
            return None

    def _send_to_platforms(self, summary: str, summary_with_call_to_action: str) -> None:
        """Send summary to Discord and optionally Twitter."""
        try:
            self._send_to_discord(summary)
            self._prompt_twitter_post(summary_with_call_to_action)
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
