# services/summary_generator.py
import os
import pandas as pd
from typing import Tuple, Optional, List

from models.discord_message import DiscordMessage
from services.chunk_processor import ChunkProcessor
from services.bullet_processor import BulletProcessor
from services.summary_finalizer import SummaryFinalizer
from utils.logging_config import setup_logging

class SummaryGenerator:
    def __init__(self, api_key: str):
        self.logger = setup_logging()
        self.chunk_processor = ChunkProcessor()
        self.bullet_processor = BulletProcessor(api_key)
        self.summary_finalizer = SummaryFinalizer(api_key)

    def generate_summary(self, df: pd.DataFrame, days_covered: int) -> Tuple[Optional[str], Optional[str]]:
        try:
            if df.empty:
                self.logger.error("Empty DataFrame provided")
                return None, None

            self.logger.info(f"Converting {len(df)} rows to messages...")
            messages = self._convert_df_to_messages(df)
            if not messages:
                self.logger.error("No valid messages could be converted from DataFrame")
                return None, None

            self.logger.info(f"Splitting {len(messages)} messages into chunks...")
            chunks = self.chunk_processor.split_messages_into_chunks(messages)
            if not chunks:
                self.logger.error("No chunks were generated from messages")
                return None, None
            self.logger.info(f"Generated {len(chunks)} chunks")

            self.logger.info("Processing chunks to generate bullets...")
            bullets = self.bullet_processor.process_chunks(chunks)
            if not bullets:
                self.logger.error("No bullets were generated from chunks")
                return None, None
            self.logger.info(f"Generated {len(bullets)} bullets")

            self.logger.info("Creating final summary...")
            summary, summary_with_cta = self.summary_finalizer.create_final_summary(bullets, days_covered)
            if not summary or not summary_with_cta:
                self.logger.error("Failed to create final summary")
                return None, None
            
            # Validate final summary contains bullet points
            if not any(line.strip().startswith('-') for line in summary.split('\n')):
                self.logger.error("Final summary contains no bullet points")
                return None, None

            self.logger.info("Summary generation completed successfully")
            return summary, summary_with_cta
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}", exc_info=True)
            return None, None

    def _convert_df_to_messages(self, df: pd.DataFrame) -> List[DiscordMessage]:
        messages = []
        errors = 0
        for idx, row in df.iterrows():
            try:
                # Validate required fields are present
                required_fields = ['channel_id', 'channel_category', 'channel_name', 
                                 'message_id', 'message_content', 'author_name']
                missing_fields = [field for field in required_fields if field not in row or pd.isna(row[field])]
                if missing_fields:
                    self.logger.warning(f"Row {idx} missing required fields: {missing_fields}")
                    continue

                message = DiscordMessage(
                    channel_id=str(row['channel_id']),
                    channel_category=str(row['channel_category']),
                    channel_name=str(row['channel_name']),
                    message_id=str(row['message_id']),
                    message_content=str(row['message_content']),
                    author_name=str(row['author_name']),
                    timestamp=str(row.get('message_timestamp', ''))
                )
                
                # Validate message content is not empty
                if not message.message_content.strip():
                    self.logger.warning(f"Row {idx} has empty message content")
                    continue
                    
                messages.append(message)
            except Exception as e:
                self.logger.warning(f"Error converting row {idx} to DiscordMessage: {e}")
                errors += 1
                if errors > len(df) * 0.5:  # If more than 50% of rows fail
                    raise ValueError("Too many errors converting DataFrame rows to messages")
                continue
                
        if not messages:
            raise ValueError("No valid messages could be created from DataFrame")
            
        return messages
