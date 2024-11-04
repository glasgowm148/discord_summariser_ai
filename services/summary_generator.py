# services/summary_generator.py
import logging
import os
import re
from typing import List, Optional, Tuple

import pandas as pd

from models.discord_message import DiscordMessage
from services.base_service import BaseService
from services.bullet_processor import BulletPoint, BulletProcessor
from services.chunk_processor import ChunkProcessor
from services.summary_finalizer import SummaryFinalizer
from utils.logging_config import setup_logging
from utils.prompts import SummaryPrompts  # Change to absolute import


class SummaryGenerator(BaseService):
    SERVER_ID = "668903786361651200"  # Replace with your actual server ID

    def __init__(
        self, 
        api_key: str, 
        chunk_processor: Optional[ChunkProcessor] = None,
        bullet_processor: Optional[BulletProcessor] = None,
        summary_finalizer: Optional[SummaryFinalizer] = None
    ):
        self.logger = setup_logging()
        
        # Use provided dependencies or create default ones
        self.chunk_processor = chunk_processor or ChunkProcessor()
        
        # If no bullet_processor is provided, create a default one
        if bullet_processor is None:
            from services.service_factory import ServiceFactory
            factory = ServiceFactory.get_instance()
            self.bullet_processor = factory.create_bullet_processor(api_key, self.SERVER_ID)
        else:
            self.bullet_processor = bullet_processor
        
        self.summary_finalizer = summary_finalizer or SummaryFinalizer(api_key)

    def initialize(self):
        # Implement the initialization logic here
        self.logger.info("SummaryGenerator initialized")
        # Any other setup code can go here

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
            bullets = self.bullet_processor.process_chunks(chunks)
            if not bullets:
                self.logger.error("No bullets were generated from chunks")
                return None, None, None
            self.logger.info(f"Generated {len(bullets)} bullets")

            self.logger.info("Creating final summaries...")
            discord_summary, discord_summary_with_cta, reddit_summary = (
                self.summary_finalizer.create_final_summary(bullets, days_covered)
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
            self.logger.error(f"Error generating summary: {e}", exc_info=True)
            return None, None, None

    def _convert_df_to_messages(self, df: pd.DataFrame) -> List[DiscordMessage]:
        messages = []
        server_id = os.getenv(
            "DISCORD_SERVER_ID"
        )  # Retrieve the server ID from environment variables

        for index, row in df.iterrows():
            try:
                message = DiscordMessage(
                    server_id=server_id,  # Use the hardcoded server ID
                    channel_id=row["channel_id"],
                    channel_category=row["channel_category"],
                    channel_name=row["channel_name"],
                    message_id=row["message_id"],
                    message_content=row["message_content"],
                    author_name=row["author_name"],
                    timestamp=row["message_timestamp"],  # Use the correct column name
                    # Do NOT include discord_link here
                )
                messages.append(message)
            except Exception as e:
                # Log the error with row details
                logging.warning(
                    f"Error converting row {index} to DiscordMessage: {e}. Row data: {row.to_dict()}"
                )
                continue

        if not messages:
            raise ValueError("Too many errors converting DataFrame rows to messages")

        return messages

    def _create_bullet_point(self, text: str) -> BulletPoint:
        bullet = BulletPoint(content=text)

        if not text.strip().startswith("-"):
            bullet.validation_messages.append("Does not start with '-'")
            return bullet

        # Extract project name
        project_match = re.search(r"\*\*([^*]+)\*\*", text)
        if project_match:
            bullet.project_name = project_match.group(1).strip()

        # Extract channel_id and message_id from the text
        discord_match = re.search(
            r"https://discord\.com/channels/(\d+)/(\d+)/(\d+)", text
        )
        if discord_match:
            bullet.discord_link = discord_match.group(0)
            bullet.channel_id = discord_match.group(2)  # Channel ID is the second group
            bullet.message_id = discord_match.group(3)  # Message ID is the third group

            print(f"Extracted Discord Link: {bullet.discord_link}")
            print(f"Extracted Channel ID: {bullet.channel_id}")
            print(f"Extracted Message ID: {bullet.message_id}")

            # Validate the extracted link
            if not self._validate_discord_link(bullet.discord_link):
                bullet.validation_messages.append("Invalid Discord link format")
                print("Invalid Discord link detected.")
                return bullet
        else:
            bullet.validation_messages.append("Missing Discord link")
            print("No Discord link found in the bullet.")

        # Use the correct author name in the bullet point
        bullet.author_name = self.author_name  # Ensure this is set correctly

        bullet.is_valid = True
        return bullet
