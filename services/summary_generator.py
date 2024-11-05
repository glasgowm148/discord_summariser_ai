# services/summary_generator.py
import logging
import os
from typing import List, Optional, Tuple

import pandas as pd
from openai import OpenAI

from models.discord_message import DiscordMessage
from services.base_service import BaseService
from helpers.processors.bullet_processor import BulletPoint, BulletProcessor
from helpers.processors.chunk_processor import ChunkProcessor
from services.summary_finalizer import SummaryFinalizer
from services.hackmd_service import HackMDService
from services.social_media.discord_service import DiscordService
from utils.logging_config import setup_logging


class SummaryGenerator(BaseService):
    MAX_DISCORD_BULLET_POINTS = 5  # Maximum number of bullet points for Discord output

    def __init__(
        self, 
        api_key: str, 
        chunk_processor: Optional[ChunkProcessor] = None,
        bullet_processor: Optional[BulletProcessor] = None,
        summary_finalizer: Optional[SummaryFinalizer] = None,
        hackmd_service: Optional[HackMDService] = None,
        discord_service: Optional[DiscordService] = None,
        openai_client: Optional[OpenAI] = None,
        post_to_hackmd: bool = False
    ):
        """Initialize with required dependencies."""
        super().__init__()  # Call parent class initializer
        
        # Use provided dependencies or create default ones through service factory
        from services.service_factory import ServiceFactory
        factory = ServiceFactory.get_instance()
        
        self.chunk_processor = chunk_processor or factory.create_chunk_processor()
        self.bullet_processor = bullet_processor or factory.create_bullet_processor(api_key, os.getenv('DISCORD_SERVER_ID', ''))
        self.summary_finalizer = summary_finalizer or factory.create_summary_finalizer(api_key)
        self.hackmd_service = hackmd_service or factory.create_hackmd_service()
        self.discord_service = discord_service or factory.create_discord_service()
        self.openai_client = openai_client or OpenAI(api_key=api_key)
        self.post_to_hackmd = post_to_hackmd
        
        # Call initialize method
        self.initialize()

    def initialize(self) -> None:
        """
        Initialize service-specific resources.
        
        This method is required by the BaseService abstract class.
        For SummaryGenerator, we'll do basic logging and validation.
        """
        self.logger.info("Initializing SummaryGenerator")
        
        # Validate that required dependencies are set
        if not all([
            self.chunk_processor, 
            self.bullet_processor, 
            self.summary_finalizer, 
            self.hackmd_service, 
            self.discord_service,
            self.openai_client
        ]):
            self.handle_error(
                ValueError("One or more required dependencies are not initialized"),
                {"context": "SummaryGenerator initialization"}
            )

    def generate_summary(
        self, df: pd.DataFrame, days_covered: int
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        try:
            if df.empty:
                self.logger.error("Empty DataFrame provided")
                return None, None, None

            self.logger.info(f"Converting {len(df)} rows to messages...")
            messages = self._convert_df_to_messages(df)
            if not messages:
                self.logger.error("No valid messages could be converted from DataFrame")
                return None, None, None

            self.logger.info(f"Splitting {len(messages)} messages into chunks...")
            chunks = self.chunk_processor.split_messages_into_chunks(messages)
            if not chunks:
                self.logger.error("No chunks were generated from messages")
                return None, None, None
            self.logger.info(f"Generated {len(chunks)} chunks")

            self.logger.info("Processing chunks to generate bullets...")
            all_bullets = self.bullet_processor.process_chunks(chunks)
            if not all_bullets:
                self.logger.error("No bullets were generated from chunks")
                return None, None, None
            self.logger.info(f"Generated {len(all_bullets)} bullets")

            # Curate the most significant 5 points using GPT-4o
            discord_bullets = self._curate_most_significant_points(all_bullets)

            # Create HackMD note for full summary if enabled
            hackmd_url = None
            if self.post_to_hackmd:
                hackmd_url = self.hackmd_service.create_note(
                    title=f"Discord Summary - Last {days_covered} Days",
                    content="\n".join(f"- {bullet}" for bullet in all_bullets)
                )

                if not hackmd_url:
                    self.logger.warning("Failed to create HackMD note.")

            self.logger.info("Creating final summaries...")
            # Use curated bullets for Discord summary, but pass ALL bullets for comprehensive summary
            discord_summary, discord_summary_with_cta, reddit_summary = (
                self.summary_finalizer.create_final_summary(
                    [str(bullet) for bullet in all_bullets], 
                    days_covered, 
                    hackmd_url  # Pass HackMD URL to be included in summary
                )
            )

            if not discord_summary or not discord_summary_with_cta:
                self.logger.error("Failed to create Discord summary")
                return None, None, None

            if not reddit_summary:
                self.logger.error("Failed to create Reddit summary")
                return None, None, None

            self.logger.info("Summary generation completed successfully")
            return discord_summary, discord_summary_with_cta, reddit_summary

        except Exception as e:
            self.handle_error(e, {"context": "Summary generation"})
            return None, None, None

    def _curate_most_significant_points(self, bullets: List[str]) -> List[str]:
        """
        Use GPT-4o to select the 5 most significant points while maintaining syntax.
        
        :param bullets: List of all generated bullet points
        :return: List of 5 most significant bullet points
        """
        try:
            # Prepare the prompt for point curation
            prompt = (
                "You are an expert at summarizing complex information. From the following list of updates, "
                "select the TOP 5 MOST SIGNIFICANT points. Consider:\n"
                "- Overall impact and importance\n"
                "- Uniqueness of the information\n"
                "- Potential long-term significance\n"
                "- Diversity of topics\n\n"
                "Maintain the EXACT original formatting of each bullet point. Do not modify the syntax, "
                "emojis, or structure. Just select the most crucial 5.\n\n"
                "Here are all the points:\n" + 
                "\n".join(f"- {bullet}" for bullet in bullets)
            )

            # Call GPT-4o to curate points
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Changed from GPT-4o to GPT-4o-mini
                messages=[
                    {"role": "system", "content": "You are an expert summarization assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.2  # Low temperature for consistent selection
            )

            # Parse the AI's selected points
            selected_summary = response.choices[0].message.content
            selected_updates = [
                line.strip().lstrip('- ') 
                for line in selected_summary.split('\n') 
                if line.strip().startswith('- ')
            ]

            # Ensure we have exactly 5 points or fall back to first 5
            selected_updates = selected_updates[:5] if len(selected_updates) >= 5 else bullets[:5]

            return selected_updates

        except Exception as e:
            self.logger.warning(f"Failed to curate points with AI: {e}")
            # Fallback to first 5 points if AI curation fails
            return bullets[:5]

    def _convert_df_to_messages(self, df: pd.DataFrame) -> List[DiscordMessage]:
        messages = []
        server_id = os.getenv("DISCORD_SERVER_ID")

        for index, row in df.iterrows():
            try:
                message = DiscordMessage(
                    server_id=server_id,
                    channel_id=row["channel_id"],
                    channel_category=row["channel_category"],
                    channel_name=row["channel_name"],
                    message_id=row["message_id"],
                    message_content=row["message_content"],
                    author_name=row["author_name"],
                    timestamp=row["message_timestamp"],
                )
                messages.append(message)
            except Exception as e:
                self.handle_error(
                    e, 
                    {
                        "context": "Converting DataFrame row to DiscordMessage", 
                        "row_index": index, 
                        "row_data": row.to_dict()
                    }
                )
                continue

        if not messages:
            raise ValueError("Too many errors converting DataFrame rows to messages")

        return messages
