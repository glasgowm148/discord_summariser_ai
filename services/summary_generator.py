# services/summary_generator.py
import logging
import os
from typing import List, Optional, Tuple
import re
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
            # ULTRA VERBOSE INITIAL DATA LOGGING
            print("\n" + "=" * 120)
            print("INITIAL DATAFRAME ANALYSIS")
            print("=" * 120)
            print(f"Total rows: {len(df)}")
            print("\nDataFrame Columns:")
            print(df.columns)
            
            # Detailed channel analysis
            print("\nChannel Distribution:")
            channel_counts = df['channel_name'].value_counts()
            print(channel_counts)
            
            # Sample rows from each channel
            print("\nSample Rows by Channel:")
            #for channel, count in channel_counts.items():
            #    print(f"\n{channel} Channel (Total: {count} messages):")
            #    channel_sample = df[df['channel_name'] == channel].head(3)
            #    for _, row in channel_sample.iterrows():
            #        print(f"  Author: {row['author_name']}")
            #        print(f"  Content: {row['message_content']}")
            #        print(f"  Timestamp: {row['message_timestamp']}")
             #       print("  ---")

            if df.empty:
                self.logger.error("Empty DataFrame provided")
                return None, None, None

            self.logger.info(f"Converting {len(df)} rows to messages...")
            messages = self._convert_df_to_messages(df)
            if not messages:
                self.logger.error("No valid messages could be converted from DataFrame")
                return None, None, None

            # ULTRA VERBOSE MESSAGE CONVERSION LOGGING
            print("\n" + "=" * 120)
            print("CONVERTED MESSAGES ANALYSIS")
            print("=" * 120)
            print(f"Total converted messages: {len(messages)}")
            
            # Analyze converted messages by channel
            message_channels = {}
            for msg in messages:
                if msg.channel_name not in message_channels:
                    message_channels[msg.channel_name] = []
                message_channels[msg.channel_name].append(msg)
            
            print("\nConverted Messages by Channel:") #correct here
            #for channel, channel_messages in message_channels.items():
            #    print(f"\n{channel} Channel (Total: {len(channel_messages)} messages):")
            #    for msg in channel_messages[:5]:  # Show first 5 messages
             #       print(f"  Author: {msg.author_name}")
            #        print(f"  Content: {msg.message_content}")
             #       print(f"  Timestamp: {msg.timestamp}")
             #       print("  ---")

            self.logger.info(f"Splitting {len(messages)} messages into chunks...")
            chunks = self.chunk_processor.split_messages_into_chunks(messages)
            if not chunks:
                self.logger.error("No chunks were generated from messages")
                return None, None, None
            self.logger.info(f"Generated {len(chunks)} chunks")

            # ULTRA VERBOSE CHUNK LOGGING
            print("\n" + "=" * 120)
            print("CHUNK GENERATION DIAGNOSTIC")
            print("=" * 120)
            for i, chunk in enumerate(chunks, 1):
                print(f"Chunk {i}:")
                print(f"  Length: {len(chunk)} characters")
                
                # Extract and analyze channels in this chunk
                chunk_channels = set(re.findall(r'Channel Name: (\w+)', chunk))
                print(f"  Channels: {', '.join(chunk_channels)}")

            self.logger.info("Processing chunks to generate bullets...")
            
            # Collect bullets from ALL chunks
            all_bullets = []
            for i, chunk in enumerate(chunks, 1):
                self.logger.info(f"Processing Chunk {i}/{len(chunks)}")
                chunk_bullets = self.bullet_processor.process_chunks([chunk])
                
                # Log chunk-specific bullet details
                print(f"\nChunk {i} Bullets:")
                for bullet in chunk_bullets:
                    print(f"  - {bullet}")
                
                all_bullets.extend(chunk_bullets)

            if not all_bullets:
                self.logger.error("No bullets were generated from chunks")
                return None, None, None
            self.logger.info(f"Generated {len(all_bullets)} total bullets")

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
        # ULTRA VERBOSE LOGGING
        print("\n" + "=" * 80)
        print("MESSAGE CONVERSION DETAILS")
        print("=" * 80)
        
        # Log DataFrame columns and first few rows
        print("DataFrame Columns:")
        print(df.columns)
        print("\nFirst few rows:")
        print(df.head())
        
        # Log unique channels and their message counts
        print("\nUnique Channels and Message Counts:")
        channel_counts = df['channel_name'].value_counts()
        print(channel_counts)

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

        # Log converted messages
        print("\nConverted Messages:")
        print(f"Total messages: {len(messages)}")
        print("Sample messages:")
        for msg in messages[:5]:
            print(f"Channel: {msg.channel_name}, Author: {msg.author_name}, Content: {msg.message_content[:100]}...")

        if not messages:
            raise ValueError("Too many errors converting DataFrame rows to messages")

        return messages
