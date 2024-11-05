"""Process chunks of text into natural paragraphs."""
import re
from typing import List, Optional
from difflib import SequenceMatcher

from openai import OpenAI

from config.settings import MAX_RETRIES, MIN_BULLETS_PER_CHUNK
from models.bullet_point import BulletPoint
from services.base_service import BaseService
from helpers.processors.bullet_validator import BulletValidator
from helpers.processors.discord_link_processor import DiscordLinkProcessor
from helpers.processors.text_processor import TextProcessor
from utils.prompts import SummaryPrompts


class BulletProcessor(BaseService):
    """Processes text chunks into validated updates."""

    def __init__(
        self,
        text_processor: TextProcessor,
        bullet_validator: BulletValidator,
        discord_link_processor: DiscordLinkProcessor,
        openai_client: OpenAI
    ):
        """Initialize with required dependencies."""
        super().__init__()
        self.text_processor = text_processor
        self.validator = bullet_validator
        self.link_processor = discord_link_processor
        self.client = openai_client
        self.total_updates = 0
        self._last_processed_bullets: List[BulletPoint] = []

    # Rest of the code remains the same as in the previous version
    def initialize(self) -> None:
        """No initialization needed as dependencies are injected."""
        pass

    def process_chunks(self, chunks: List[str]) -> List[str]:
        """Process multiple chunks into updates."""
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
                processed_chunk = self.text_processor.optimize_chunk_size(chunk)
                chunk_updates = self._process_single_chunk(processed_chunk, i)
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
        deduplicated_updates = self._deduplicate_updates(collected_updates)

        # Create BulletPoint objects for the deduplicated updates
        self._last_processed_bullets = [self._create_update_point(update) for update in deduplicated_updates]

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

                # Modify extraction to handle multiple updates more robustly
                new_updates = self._extract_updates_from_chunk(chunk, retry_count, len(chunk_updates))
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

    def _deduplicate_updates(self, updates: List[str]) -> List[str]:
        """
        Advanced deduplication that preserves updates with different Discord links.
        
        Removes duplicates while considering:
        1. Core content similarity
        2. Presence of unique Discord links
        3. Information richness
        """
        unique_updates = []
        processed_contents = []

        for update in updates:
            # Extract core content and Discord link
            core_content = self.text_processor.extract_core_content(update)
            discord_link = self.text_processor.extract_discord_url(update)
            
            # Check if this update is a potential duplicate
            is_duplicate = False
            for idx, existing_content in enumerate(processed_contents):
                # More nuanced similarity check
                # Use difflib's SequenceMatcher for similarity
                similarity_ratio = SequenceMatcher(None, core_content, existing_content).ratio()
                
                # If updates are very similar
                if similarity_ratio > 0.7:
                    # Compare Discord links
                    existing_link = self.text_processor.extract_discord_url(unique_updates[idx])
                    
                    # If links are different, keep both updates
                    if discord_link and existing_link and discord_link != existing_link:
                        continue
                    
                    # If existing update is less informative, replace it
                    if self._get_update_score(update) > self._get_update_score(unique_updates[idx]):
                        unique_updates[idx] = update
                        processed_contents[idx] = core_content
                    
                    is_duplicate = True
                    break
            
            # Add update if not a duplicate
            if not is_duplicate:
                unique_updates.append(update)
                processed_contents.append(core_content)

        return unique_updates

    def _get_update_score(self, update: str) -> int:
        """Calculate an information score for an update."""
        # Count words
        word_count = len(update.split())
        
        # Bonus for having a Discord link
        has_link = 5 if self.text_processor.extract_discord_url(update) else 0
        
        # Bonus for technical terms
        has_technical_terms = 3 if re.search(
            r'(?i)(implementation|development|infrastructure|protocol|system|platform|version|strategy)',
            update
        ) else 0
        
        return word_count + has_link + has_technical_terms

    def _extract_updates_from_chunk(self, chunk: str, retry_count: int, current_updates: int) -> List[str]:
        """Extract updates from chunk using OpenAI API with more robust splitting."""
        temperature = min(0.7 + (retry_count * 0.05), 0.95)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SummaryPrompts.get_system_prompt()},
                    {"role": "user", "content": SummaryPrompts.get_user_prompt(chunk, current_updates)},
                ],
                temperature=temperature,
                max_tokens=4000,
            )

            summary = response.choices[0].message.content
            
            # More robust splitting strategy
            # 1. First, try splitting by emoji-prefixed lines
            updates = re.split(r'\n(?=[\U0001F300-\U0001F9FF])', summary)
            
            # If that fails, try alternative splitting
            if len(updates) <= 1:
                # Split by lines starting with bullet points or emojis
                updates = re.split(r'\n(?=[-•\U0001F300-\U0001F9FF])', summary)
            
            # Clean and filter updates
            updates = [u.strip() for u in updates if u.strip()]
            
            # Ensure each update starts with an emoji
            updates = [
                f"🔹 {u}" if not re.match(r'^[\U0001F300-\U0001F9FF]', u.strip()) else u
                for u in updates
            ]

            return updates

        except Exception as e:
            self.handle_error(e, {"context": "OpenAI API call"})
            raise

    def _create_update_point(self, text: str) -> BulletPoint:
        """Create an update point object from text."""
        update = BulletPoint(content=text)

        # Extract channel name
        channel_match = re.search(r'Channel:\s*([^\n]+)', text)
        if channel_match:
            update.channel_name = channel_match.group(1).strip()

        # Extract project name
        project_match = re.search(r'\*\*([^*]+)\*\*', text)
        if project_match:
            project_name = project_match.group(1).strip()
            # Simplify project name
            simplified_name = self.text_processor.simplify_project_name(project_name)
            # Replace original project name with simplified version
            update.content = text.replace(f"**{project_name}**", f"**{simplified_name}**")
            update.project_name = simplified_name

        # Extract Discord link components
        discord_match = re.search(r'https://discord\.com/channels/(\d+)/(\d+)/(\d+)', text)
        if discord_match:
            update.discord_link = discord_match.group(0)
            update.channel_id = discord_match.group(2)
            update.message_id = discord_match.group(3)

        return update
