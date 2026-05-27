"""Interactive summary workflow separated from CLI entrypoint."""

from pathlib import Path
from typing import Optional

from config.app_config import AppConfig
from services.base_service import BaseService
from services.csv_loader import CsvLoaderService
from services.posting_adapters import PostingAdapters
from services.summary_generator import SummaryGenerator


class SummaryWorkflow(BaseService):
    """Load latest export, generate summaries, and optionally post them."""

    def __init__(
        self,
        config: AppConfig,
        csv_loader: Optional[CsvLoaderService] = None,
        summary_generator: Optional[SummaryGenerator] = None,
        posting: Optional[PostingAdapters] = None,
    ):
        super().__init__()
        self.config = config
        self.csv_loader = csv_loader or CsvLoaderService()
        self.summary_generator = summary_generator or SummaryGenerator(config.openai_api_key)
        self.posting = posting or PostingAdapters()

    def get_latest_summary(self) -> Optional[str]:
        """Get latest Discord summary from output/sent_summaries.md."""
        try:
            summaries_file = self.config.output_dir / "sent_summaries.md"
            if not summaries_file.exists():
                return None

            content = summaries_file.read_text().strip()
            if not content:
                return None

            summaries = content.split("\n## ")
            discord_summaries = [s for s in summaries if "Discord Summary" in s.split("\n")[0]]
            if not discord_summaries:
                return None

            latest = "## " + discord_summaries[-1]
            return "\n".join(latest.split("\n")[2:])
        except Exception as exc:
            self.handle_error(exc, {"context": "Reading latest summary"})
            return None

    async def run(self) -> None:
        """Execute interactive summarisation workflow."""
        self.logger.info("Starting execution...")
        df, _, days_covered = self.csv_loader.load_latest_csv(self.config.output_dir)

        latest_summary = self.get_latest_summary()
        if latest_summary:
            print("\nLatest summary found:")
            print("-" * 50)
            print(latest_summary)
            print("-" * 50)
            if input("\nUse this summary instead of generating a new one? (y/n): ").lower() == "y":
                print("\nUsing existing summary. Done!")
                return

        print("\nGenerating initial summary bullets...")
        discord_summary, discord_summary_with_cta, reddit_summary = (
            self.summary_generator.generate_summary(df, days_covered)
        )

        if not discord_summary or not reddit_summary:
            self.logger.error("Failed to generate initial summary")
            return

        generated_bullets = self.summary_generator.bullet_processor.get_last_processed_bullets()
        self._print_bullets(generated_bullets)

        if input("\nGenerate Discord summary from these bullets? (y/n): ").lower() == "y":
            self._preview("Discord Summary", discord_summary)
            if input("\nSend this summary to Discord? (y/n): ").lower() == "y":
                self._send_to_discord(discord_summary)

        if input("\nGenerate Reddit summary from these bullets? (y/n): ").lower() == "y":
            self._preview("Reddit Summary", reddit_summary)
            if input("\nPost this summary to Reddit? (y/n): ").lower() == "y":
                self.posting.discord_service().send_reddit_summary(reddit_summary)
                await self._post_to_reddit(reddit_summary)

        if input("\nGenerate Twitter summary from these bullets? (y/n): ").lower() == "y":
            bullet_strings = [bullet.content for bullet in generated_bullets]
            twitter_summary, twitter_summary_with_cta, _ = (
                self.summary_generator.summary_finalizer.create_final_summary(bullet_strings, days_covered)
            )
            if twitter_summary:
                formatted = self.summary_generator.summary_finalizer.format_for_social_media(
                    twitter_summary_with_cta,
                    "twitter",
                )
                self._preview("Formatted Twitter summary", formatted)
                if input("\nPost this summary to Twitter? (y/n): ").lower() == "y":
                    self.posting.twitter_service().send_tweet(formatted)
            else:
                self.logger.error("Twitter summary generation failed")

        if input("\nGenerate Meta platforms summary from these bullets? (y/n): ").lower() == "y":
            bullet_strings = [bullet.content for bullet in generated_bullets]
            meta_summary, meta_summary_with_cta, _ = (
                self.summary_generator.summary_finalizer.create_final_summary(bullet_strings, days_covered)
            )
            if meta_summary:
                await self.posting.meta_service().prompt_and_post(meta_summary_with_cta)
            else:
                self.logger.error("Meta summary generation failed")

    def _send_to_discord(self, summary: str) -> None:
        days_covered = self.csv_loader.get_days_covered()
        service = self.posting.discord_service()
        if days_covered > 5:
            service.send_weekly_message(summary)
        else:
            service.send_daily_message(summary)

    async def _post_to_reddit(self, reddit_summary: str) -> None:
        days = self.csv_loader.get_days_covered()
        title = f"Ergo Development Update - {days} Day Roundup"
        if await self.posting.reddit_service().post_to_reddit(title, reddit_summary):
            self.logger.info("Successfully posted to Reddit")
        else:
            self.logger.error("Failed to post to Reddit")

    def _preview(self, title: str, content: str) -> None:
        print(f"\n{title}:")
        print("-" * 50)
        print(content)
        print("-" * 50)

    def _print_bullets(self, bullets) -> None:
        print("\nGenerated Summary Bullets:")
        print("-" * 50)
        for bullet in bullets:
            print(bullet.content)
        print("-" * 50)
