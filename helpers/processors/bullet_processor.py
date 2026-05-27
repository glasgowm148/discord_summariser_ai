"""Process chunks of text into natural paragraphs."""
import re
from typing import List, Optional

from openai import OpenAI

from config.settings import MAX_RETRIES, MIN_BULLETS_PER_CHUNK
from models.bullet_point import BulletPoint
from services.base_service import BaseService
from helpers.processors.bullet_validator import BulletValidator
from helpers.processors.discord_link_processor import DiscordLinkProcessor
from helpers.processors.text_processor import TextProcessor
from helpers.processors.update_extractor import UpdateExtractor
from helpers.processors.update_deduplicator import UpdateDeduplicator


class BulletProcessor(BaseService):
    """Processes text chunks into validated updates."""

    def __init__(
        self,
        text_processor: TextProcessor,
        bullet_validator: BulletValidator,
        discord_link_processor: DiscordLinkProcessor,
        update_extractor: UpdateExtractor,
        update_deduplicator: UpdateDeduplicator,
        openai_client: OpenAI
    ):
        """Initialize with required dependencies."""
        super().__init__()
        self.text_processor = text_processor
        self.validator = bullet_validator
        self.link_processor = discord_link_processor
        self.update_extractor = update_extractor
        self.update_deduplicator = update_deduplicator
        self.client = openai_client
        self.total_updates = 0
        self._last_processed_bullets: List[BulletPoint] = []
        
        # Call initialize method
        self.initialize()

    def initialize(self) -> None:
        """
        Initialize service-specific resources.
        
        This method is required by the BaseService abstract class.
        For BulletProcessor, we'll do basic logging and validation.
        """
        self.logger.info("Initializing BulletProcessor")
        
        # Validate that required dependencies are set
        if not all([
            self.text_processor, 
            self.validator, 
            self.link_processor, 
            self.update_extractor, 
            self.update_deduplicator,
            self.client
        ]):
            self.handle_error(
                ValueError("One or more required dependencies are not initialized"),
                {"context": "BulletProcessor initialization"}
            )

    def process_chunks(self, chunks: List[str]) -> List[str]:
        """Process multiple chunks into updates."""
        self.logger.info("Processing %s chunks", len(chunks))
        for i, chunk in enumerate(chunks, 1):
            chunk_channels = set(re.findall(r'Channel Name: (\w+)', chunk))
            self.logger.debug(
                "Chunk %s length=%s channels=%s",
                i,
                len(chunk),
                ", ".join(sorted(chunk_channels)),
            )
        
        collected_updates = []
        self.total_updates = 0
        self._last_processed_bullets = []  # Reset last processed bullets

        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"Starting update generation for {len(chunks)} chunks")
        self.logger.info("=" * 80)

        for i, chunk in enumerate(chunks, 1):
            self.logger.info(f"\n📝 Processing Chunk {i}/{len(chunks)}")
            self.logger.info("-" * 80)

            try:
                
                chunk_updates = self._process_single_chunk(chunk, i)
                if chunk_updates:
                    collected_updates.extend(chunk_updates)
                    self.total_updates = len(collected_updates)
                    self.logger.info(f"\n✅ Chunk {i} Complete")
                    self.logger.info(f"   Updates from this chunk: {len(chunk_updates)}")
                    self.logger.info(f"   Total updates so far: {self.total_updates}")
                    self.logger.info("-" * 80)
            except Exception as e:
                self.handle_error(e, {"chunk_index": i})
                continue

        if not collected_updates:
            raise ValueError("No valid updates were generated from any chunks")

        # Deduplicate updates
        deduplicated_updates = self.update_deduplicator.deduplicate_updates(collected_updates)

        # Create BulletPoint objects for the deduplicated updates
        self._last_processed_bullets = [self._create_update_point(update) for update in deduplicated_updates]

        self.logger.info(
            "Collected %s updates, deduplicated to %s",
            len(collected_updates),
            len(deduplicated_updates),
        )
        for update in deduplicated_updates:
            self.logger.debug("Deduplicated update: %s", update)

        return deduplicated_updates

    def get_last_processed_bullets(self) -> List[BulletPoint]:
        """Retrieve the last processed bullets."""
        return self._last_processed_bullets

    def _process_single_chunk(self, chunk: str, chunk_num: int) -> List[str]:
        """Process a single chunk into natural paragraphs."""
        chunk_updates = []
        retry_count = 0

        while retry_count < MAX_RETRIES and len(chunk_updates) < MIN_BULLETS_PER_CHUNK:
            try:
                self.logger.info(f"\n🔄 Attempt {retry_count + 1} for Chunk {chunk_num}")
                self.logger.info(f"   Current update count: {len(chunk_updates)}/{MIN_BULLETS_PER_CHUNK} minimum")
                self.logger.info("   " + "-" * 40)

                # Extract updates using the dedicated extractor
                new_updates = self.update_extractor.extract_updates_from_chunk(chunk, retry_count, len(chunk_updates))
                if not new_updates:
                    self.logger.warning("   ⚠️  No updates returned from API")
                    retry_count += 1
                    continue

                self.logger.info(f"\n📋 Processing {len(new_updates)} new updates:")
                valid_new_updates = []

                for i, update_text in enumerate(new_updates, 1):
                    # Ensure each update starts with an emoji and has a clear structure
                    if not re.match(r'^[\U0001F300-\U0001F9FF]', update_text.strip()):
                        update_text = f"🔹 {update_text}"

                    update = self._create_update_point(update_text)
                    is_valid, messages = self.validator.validate_bullet(update)
                    update.is_valid = is_valid
                    update.validation_messages = messages

                    # Format update output
                    self.logger.info(f"\n🔹 Update {i}:")
                    self.logger.info(f"   {update_text}")
                    self.logger.info(f"   Validation: {self.validator.validate_bullet_verbose(update)}")

                    if update.is_valid:
                        # Clean bot references and standardize text
                        cleaned_text = self.text_processor.standardize_text(update.content)
                        valid_new_updates.append(cleaned_text)
                    elif update.discord_link:
                        # Try to fix the Discord link
                        fixed_update = self.link_processor.fix_discord_link(update.content, chunk)
                        if fixed_update:
                            valid_new_updates.append(fixed_update)
                        else:
                            self.logger.warning(f"   ⚠️  Could not fix Discord link: {update.discord_link}")

                if valid_new_updates:
                    self.logger.info(f"\n✨ Valid updates this attempt: {len(valid_new_updates)}/{len(new_updates)}")
                    chunk_updates.extend(valid_new_updates)
                    self.logger.info(f"📊 Progress: {len(chunk_updates)}/{MIN_BULLETS_PER_CHUNK} minimum updates")
                else:
                    self.logger.info("\n⚠️  No valid updates in this attempt")

                retry_count += 1

            except Exception as e:
                self.handle_error(e, {"retry_count": retry_count, "current_updates": len(chunk_updates)})
                retry_count += 1
                if retry_count >= MAX_RETRIES and not chunk_updates:
                    raise ValueError(f"Failed to generate valid updates after {MAX_RETRIES} attempts") from None

        return chunk_updates

    def _create_update_point(self, text: str) -> BulletPoint:
        """Create an update point object from text."""
        update = BulletPoint(content=text)

        # Extract channel name from the chunk
        channel_match = re.search(r'Channel Name:\s*(\w+)', text)
        if channel_match:
            update.channel_name = channel_match.group(1)
            self.logger.info(f"Extracted channel name: {update.channel_name}")

        # Extract project name more intelligently
        # First, try to find a project name that is not a channel category
        project_match = re.search(r'\*\*([^*]+)\*\*', text)
        
        # Extract Discord link components first
        discord_match = re.search(r'https://discord\.com/channels/(\d+)/(\d+)/(\d+)', text)
        if discord_match:
            update.discord_link = discord_match.group(0)
            update.channel_id = discord_match.group(2)
            update.message_id = discord_match.group(3)

        if project_match:
            project_name = project_match.group(1).strip()
            
            # Check if the project name looks like a channel category (contains '/')
            if '/' in project_name:
                # If it's a channel category and we have an extracted channel name, use that
                if update.channel_name:
                    update.project_name = update.channel_name
                    self.logger.info(f"Using channel name as project name: {update.project_name}")
                else:
                    # Fallback to a generic name if no channel name is available
                    update.project_name = 'Project'
                    self.logger.warning("No channel name found, defaulting to 'Project'")
            else:
                # Simplify project name
                simplified_name = self.text_processor.simplify_project_name(project_name)
                # Replace original project name with simplified version
                update.content = text.replace(f"**{project_name}**", f"**{simplified_name}**")
                update.project_name = simplified_name

        self.logger.info(f"Final project name: {update.project_name}")

        return update
