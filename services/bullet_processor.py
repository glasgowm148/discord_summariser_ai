"""Process chunks of text into bullet points."""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set

from openai import OpenAI

from config.settings import MAX_RETRIES, MIN_BULLETS_PER_CHUNK
from services.base_service import BaseService
from utils.prompts import SummaryPrompts


@dataclass
class BulletPoint:
    """Represents a processed bullet point."""

    content: str
    project_name: str = ""
    discord_link: str = ""
    is_valid: bool = False
    validation_messages: List[str] = field(default_factory=list)
    channel_id: str = ""
    message_id: str = ""
    channel_name: str = ""  # Added to track channel context


class BulletProcessor(BaseService):
    SERVER_ID = "668903786361651200"  # Discord server ID

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.total_bullets = 0
        self.initialize()

    def initialize(self) -> None:
        """Initialize OpenAI client."""
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            self.handle_error(e, {"context": "OpenAI client initialization"})
            raise

    def _simplify_project_name(self, project_name: str) -> str:
        """Simplify and standardize project names."""
        # Convert to lowercase for comparison
        name_lower = project_name.lower()
        
        # Remove common suffixes and descriptors
        name_lower = re.sub(r'\s+(?:implementation|update|development|improvements?|remarks|protocol|v\d+|version\s+\d+|integration)s?\s*$', '', name_lower)
        
        # Return original first word with original capitalization
        return project_name.split()[0]

    def process_chunks(self, chunks: List[str]) -> List[str]:
        """Process multiple chunks into bullet points."""
        collected_bullets = []
        self.total_bullets = 0

        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"Starting bullet point generation for {len(chunks)} chunks")
        self.logger.info("=" * 80)

        for i, chunk in enumerate(chunks, 1):
            self.logger.info(f"\n📝 Processing Chunk {i}/{len(chunks)}")
            self.logger.info("-" * 80)

            try:
                processed_chunk = self._optimize_chunk_size(chunk)
                chunk_bullets = self._process_single_chunk(processed_chunk, i)
                if chunk_bullets:
                    collected_bullets.extend(chunk_bullets)
                    self.total_bullets = len(collected_bullets)
                    self.logger.info(f"\n✅ Chunk {i} Complete")
                    self.logger.info(f"   Bullets from this chunk: {len(chunk_bullets)}")
                    self.logger.info(f"   Total bullets so far: {self.total_bullets}")
                    self.logger.info("-" * 80)
            except Exception as e:
                self.handle_error(e, {"chunk_index": i})
                continue

        if not collected_bullets:
            raise ValueError("No valid bullets were generated from any chunks")

        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"Bullet Generation Complete - Total Valid Bullets: {self.total_bullets}")
        self.logger.info("=" * 80 + "\n")

        return self._post_process_bullets(collected_bullets)

    def _optimize_chunk_size(self, chunk: str) -> str:
        """Optimize chunk size for GPT-4 processing."""
        # Extract channel name if present
        channel_match = re.search(r'Channel:\s*([^\n]+)', chunk)
        channel_name = channel_match.group(1) if channel_match else ""
        
        # Split chunk into messages if it contains message separators
        messages = chunk.split("---\n")

        # If it's a single message or doesn't use separators, return as is
        if len(messages) <= 1:
            return chunk

        # Process messages in reverse chronological order (most recent first)
        optimized_messages = []
        current_length = 0
        target_length = 100000  # Target length in characters (conservative estimate for tokens)

        for msg in messages:
            msg_length = len(msg) + 4  # Add 4 for the separator
            if current_length + msg_length > target_length:
                break
            # Add channel context if available
            if channel_name and "Channel:" not in msg:
                msg = f"Channel: {channel_name}\n{msg}"
            optimized_messages.append(msg)
            current_length += msg_length

        # Return optimized chunk
        if optimized_messages:
            return "---\n".join(optimized_messages) + "---\n"
        return messages[0] + "---\n"  # Fallback to first message if optimization fails

    def _process_single_chunk(self, chunk: str, chunk_num: int) -> List[str]:
        """Process a single chunk into bullet points."""
        chunk_bullets = []
        retry_count = 0

        while retry_count < MAX_RETRIES and len(chunk_bullets) < MIN_BULLETS_PER_CHUNK:
            try:
                self.logger.info(f"\n🔄 Attempt {retry_count + 1} for Chunk {chunk_num}")
                self.logger.info(f"   Current bullet count: {len(chunk_bullets)}/{MIN_BULLETS_PER_CHUNK} minimum")
                self.logger.info("   " + "-" * 40)

                new_bullets = self._extract_bullets_from_chunk(chunk, retry_count, len(chunk_bullets))
                if not new_bullets:
                    self.logger.warning("   ⚠️  No bullets returned from API")
                    retry_count += 1
                    continue

                self.logger.info(f"\n📋 Processing {len(new_bullets)} new bullets:")
                valid_new_bullets = []

                for i, bullet_text in enumerate(new_bullets, 1):
                    bullet = self._create_bullet_point(bullet_text)
                    validation_result = self._validate_bullet_verbose(bullet)

                    # Format bullet output
                    self.logger.info(f"\n🔹 Bullet {i}:")
                    self.logger.info(f"   {bullet_text}")
                    self.logger.info(f"   Validation: {validation_result}")

                    if bullet.is_valid:
                        # Validate Discord link format
                        if self._validate_discord_link(bullet.discord_link):
                            valid_new_bullets.append(bullet.content)
                        else:
                            # Try to fix the Discord link
                            fixed_bullet = self._fix_discord_link(bullet.content, chunk)
                            if fixed_bullet:
                                valid_new_bullets.append(fixed_bullet)
                            else:
                                self.logger.warning(f"   ⚠️  Could not fix Discord link: {bullet.discord_link}")

                if valid_new_bullets:
                    self.logger.info(f"\n✨ Valid bullets this attempt: {len(valid_new_bullets)}/{len(new_bullets)}")
                    chunk_bullets.extend(valid_new_bullets)
                    self.logger.info(f"📊 Progress: {len(chunk_bullets)}/{MIN_BULLETS_PER_CHUNK} minimum bullets")
                else:
                    self.logger.info("\n⚠️  No valid bullets in this attempt")

                retry_count += 1

            except Exception as e:
                self.handle_error(e, {"retry_count": retry_count, "current_bullets": len(chunk_bullets)})
                retry_count += 1
                if retry_count >= MAX_RETRIES and not chunk_bullets:
                    raise ValueError(f"Failed to generate valid bullets after {MAX_RETRIES} attempts") from None

        return chunk_bullets

    def _extract_bullets_from_chunk(self, chunk: str, retry_count: int, current_bullets: int) -> List[str]:
        """Extract bullet points from chunk using OpenAI API."""
        temperature = min(0.7 + (retry_count * 0.05), 0.95)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SummaryPrompts.get_system_prompt()},
                    {"role": "user", "content": SummaryPrompts.get_user_prompt(chunk, current_bullets)},
                ],
                temperature=temperature,
                max_tokens=4000,
            )

            summary = response.choices[0].message.content
            return [b.strip() for b in summary.split("\n") if b.strip().startswith("-")]

        except Exception as e:
            self.handle_error(e, {"context": "OpenAI API call"})
            raise

    def _create_bullet_point(self, text: str) -> BulletPoint:
        """Create a bullet point object from text."""
        bullet = BulletPoint(content=text)

        # Extract channel name from the bullet text if present
        channel_match = re.search(r'Channel:\s*([^\n]+)', text)
        if channel_match:
            bullet.channel_name = channel_match.group(1).strip()

        if not text.strip().startswith('-'):
            bullet.validation_messages.append("Does not start with '-'")
            return bullet

        # Extract project name
        project_match = re.search(r'\*\*([^*]+)\*\*', text)
        if project_match:
            project_name = project_match.group(1).strip()
            # Simplify project name
            simplified_name = self._simplify_project_name(project_name)
            # Replace original project name with simplified version
            bullet.content = text.replace(f"**{project_name}**", f"**{simplified_name}**")
            bullet.project_name = simplified_name

        # Extract channel_id and message_id from the text
        discord_match = re.search(r'https://discord\.com/channels/(\d+)/(\d+)/(\d+)', text)
        if discord_match:
            bullet.discord_link = discord_match.group(0)
            bullet.channel_id = discord_match.group(2)  # Channel ID is the second group
            bullet.message_id = discord_match.group(3)  # Message ID is the third group

            # Validate the extracted link
            if not self._validate_discord_link(bullet.discord_link):
                bullet.validation_messages.append("Invalid Discord link format")
                return bullet
        else:
            bullet.validation_messages.append("Missing Discord link")

        # Validate content length
        if len(text.strip()) <= 50:
            bullet.validation_messages.append("Too short")
            return bullet

        bullet.is_valid = True
        return bullet

    def _validate_discord_link(self, link: str) -> bool:
        """Validate Discord link format."""
        pattern = f"^https://discord\\.com/channels/{self.SERVER_ID}/\\d+/\\d+$"
        return bool(re.match(pattern, link))

    def _fix_discord_link(self, content: str, chunk: str) -> Optional[str]:
        """Try to fix a Discord link using message metadata from the chunk."""
        try:
            message_match = re.search(r"Message ID: (\d+)", chunk)
            channel_match = re.search(r"Channel ID: (\d+) ", chunk)

            if message_match and channel_match:
                message_id = message_match.group(1)
                channel_id = channel_match.group(1)
                correct_link = f"https://discord.com/channels/{self.SERVER_ID}/{channel_id}/{message_id}"

                # Replace the incorrect link with the correct one
                fixed_content = re.sub(
                    r"\(https://discord\.com/channels/[^)]+\)",
                    f"({correct_link})",
                    content,
                )

                return fixed_content

        except Exception as e:
            self.logger.warning(f"Error fixing Discord link: {e}")
            return None

    def _validate_bullet_verbose(self, bullet: BulletPoint) -> str:
        """Return detailed validation results for logging."""
        result = []

        if bullet.content.strip().startswith("-"):
            result.append("✓ Format")
        else:
            result.append("❌ Format")

        if bullet.discord_link:
            if self._validate_discord_link(bullet.discord_link):
                result.append("✓ Link")
            else:
                result.append("❌ Invalid Link Format")
        else:
            result.append("❌ Link")

        length = len(bullet.content.strip())
        if length > 50:
            result.append(f"✓ Length ({length})")
        else:
            result.append(f"❌ Length ({length})")

        if bullet.project_name:
            result.append(f"✓ Project: {bullet.project_name}")
        else:
            result.append("⚠️ No project")

        if bullet.channel_name:
            result.append(f"✓ Channel: {bullet.channel_name}")

        return " | ".join(result)

    def _find_related_bullets(self, bullets: List[str]) -> Dict[str, List[str]]:
        """Find groups of related bullets based on content similarity."""
        related_groups: Dict[str, List[str]] = {}
        processed_indices: Set[int] = set()

        for i, bullet in enumerate(bullets):
            if i in processed_indices:
                continue

            # Extract main topic from the bullet (usually after the project name)
            main_content = re.sub(r'\*\*[^*]+\*\*:', '', bullet).lower()
            main_content = re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', main_content)
            
            # Find related bullets
            related = []
            for j, other_bullet in enumerate(bullets):
                if j != i and j not in processed_indices:
                    other_content = re.sub(r'\*\*[^*]+\*\*:', '', other_bullet).lower()
                    other_content = re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', other_content)
                    
                    # Check for content similarity
                    if self._is_content_related(main_content, other_content):
                        related.append(other_bullet)
                        processed_indices.add(j)

            if related:
                processed_indices.add(i)
                key_topic = self._extract_key_topic(bullet)
                if key_topic in related_groups:
                    related_groups[key_topic].extend([bullet] + related)
                else:
                    related_groups[key_topic] = [bullet] + related

        return related_groups

    def _is_content_related(self, content1: str, content2: str) -> bool:
        """Check if two pieces of content are related based on shared keywords and context."""
        # Remove common words and punctuation
        words1 = set(re.findall(r'\b\w+\b', content1.lower()))
        words2 = set(re.findall(r'\b\w+\b', content2.lower()))
        
        # Calculate similarity based on shared significant words
        common_words = words1.intersection(words2)
        total_words = len(words1.union(words2))
        
        if total_words == 0:
            return False
            
        similarity_ratio = len(common_words) / total_words
        return similarity_ratio > 0.3  # Threshold for considering content related

    def _extract_key_topic(self, bullet: str) -> str:
        """Extract the key topic from a bullet point."""
        # Try to get the project name first
        project_match = re.search(r'\*\*([^*]+)\*\*', bullet)
        if project_match:
            return project_match.group(1)
        
        # Otherwise, extract key words from the content
        content = re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', bullet.lower())
        words = re.findall(r'\b\w+\b', content)
        return words[1] if len(words) > 1 else words[0] if words else "general"

    def _combine_related_bullets(self, bullets: List[str]) -> str:
        """Combine related bullets into a single comprehensive bullet point."""
        if not bullets:
            return ""

        # Extract project name from the first bullet
        project_match = re.search(r'\*\*([^*]+)\*\*', bullets[0])
        project_name = project_match.group(1) if project_match else "General"

        # Collect all Discord links
        links = []
        contents = []
        for bullet in bullets:
            # Extract Discord link
            link_match = re.search(r'\[(?:here|[^\]]+)\]\((https://discord\.com/channels/[^)]+)\)', bullet)
            if link_match:
                links.append(link_match.group(1))
            
            # Extract content without the link part
            content = re.sub(r'\[(?:here|[^\]]+)\]\(https://discord\.com/channels/[^)]+\)', '', bullet)
            content = re.sub(r'\*\*[^*]+\*\*:', '', content)
            contents.append(content.strip())

        # Combine contents and links
        combined_content = " ".join(contents)
        combined_links = ", ".join(f"[discussion {i+1}]({link})" for i, link in enumerate(links))
        
        return f"- **{project_name}**: {combined_content} Read more: {combined_links}"

    def _post_process_bullets(self, bullets: List[str]) -> List[str]:
        """Post-process bullets to merge related updates and ensure proper attribution."""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("Post-processing Bullets")
        self.logger.info("=" * 80)

        # Find groups of related bullets
        related_groups = self._find_related_bullets(bullets)

        # Process each group and other unrelated bullets
        processed_bullets = []
        processed_indices = set()

        # Combine related groups
        for topic, group in related_groups.items():
            combined_bullet = self._combine_related_bullets(group)
            if combined_bullet:
                processed_bullets.append(combined_bullet)

        # Add remaining unrelated bullets
        for i, bullet in enumerate(bullets):
            if i not in processed_indices:
                processed_bullets.append(bullet)

        # Clean up any remaining bot references
        final_bullets = []
        for bullet in processed_bullets:
            # Replace bot references with project attribution
            bullet = re.sub(
                r"(?:Bot|GroupAnonymousBot)\s+(?:highlighted|mentioned|discussed|shared|announced)",
                "The team announced",
                bullet
            )
            final_bullets.append(bullet)

        self.logger.info(f"\n✅ Post-processing complete - Final bullet count: {len(final_bullets)}")
        self.logger.info("=" * 80 + "\n")

        return final_bullets
