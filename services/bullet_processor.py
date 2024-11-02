"""Process chunks of text into bullet points."""
import re
from typing import List, Optional
from openai import OpenAI
from dataclasses import dataclass, field

from config.settings import (
    MAX_RETRIES,
    MIN_BULLETS_PER_CHUNK
)
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

class BulletProcessor(BaseService):
    SERVER_ID = "668903786361651200"  # Ergo Discord server ID

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

    def process_chunks(self, chunks: List[str]) -> List[str]:
        """Process multiple chunks into bullet points."""
        collected_bullets = []
        self.total_bullets = 0

        self.logger.info("\n" + "="*80)
        self.logger.info(f"Starting bullet point generation for {len(chunks)} chunks")
        self.logger.info("="*80)

        for i, chunk in enumerate(chunks, 1):
            self.logger.info(f"\n📝 Processing Chunk {i}/{len(chunks)}")
            self.logger.info("-"*80)
            
            try:
                processed_chunk = self._optimize_chunk_size(chunk)
                chunk_bullets = self._process_single_chunk(processed_chunk, i)
                if chunk_bullets:
                    collected_bullets.extend(chunk_bullets)
                    self.total_bullets = len(collected_bullets)
                    self.logger.info(f"\n✅ Chunk {i} Complete")
                    self.logger.info(f"   Bullets from this chunk: {len(chunk_bullets)}")
                    self.logger.info(f"   Total bullets so far: {self.total_bullets}")
                    self.logger.info("-"*80)
            except Exception as e:
                self.handle_error(e, {"chunk_index": i})
                continue

        if not collected_bullets:
            raise ValueError("No valid bullets were generated from any chunks")

        self.logger.info("\n" + "="*80)
        self.logger.info(f"Bullet Generation Complete - Total Valid Bullets: {self.total_bullets}")
        self.logger.info("="*80 + "\n")

        return self._post_process_bullets(collected_bullets)

    def _optimize_chunk_size(self, chunk: str) -> str:
        """Optimize chunk size for GPT-4 processing."""
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
                self.logger.info("   " + "-"*40)
                
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
                self.handle_error(e, {
                    "retry_count": retry_count,
                    "current_bullets": len(chunk_bullets)
                })
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
                    {"role": "user", "content": SummaryPrompts.get_user_prompt(chunk, current_bullets)}
                ],
                temperature=temperature,
                max_tokens=4000
            )
            
            summary = response.choices[0].message.content
            return [b.strip() for b in summary.split('\n') if b.strip().startswith('-')]
            
        except Exception as e:
            self.handle_error(e, {"context": "OpenAI API call"})
            raise

    def _create_bullet_point(self, text: str) -> BulletPoint:
        """Create and validate a bullet point."""
        bullet = BulletPoint(content=text)
        
        if not text.strip().startswith('-'):
            bullet.validation_messages.append("Does not start with '-'")
            return bullet

        # Extract project name
        project_match = re.search(r'\*\*([^*]+)\*\*', text)
        if project_match:
            bullet.project_name = project_match.group(1).strip()

        # Extract Discord link
        discord_match = re.search(r'\[([^\]]+)\]\((https://discord\.com/channels/[^)]+)\)', text)
        if discord_match:
            bullet.discord_link = discord_match.group(2)
        else:
            bullet.validation_messages.append("Missing Discord link")
            return bullet

        if len(text.strip()) <= 50:
            bullet.validation_messages.append("Too short")
            return bullet

        bullet.is_valid = True
        return bullet

    def _validate_discord_link(self, link: str) -> bool:
        """Validate Discord link format."""
        # Check if link matches expected format with server ID, channel ID, and message ID
        pattern = f'^https://discord\.com/channels/{self.SERVER_ID}/\\d+/\\d+$'
        return bool(re.match(pattern, link))

    def _fix_discord_link(self, content: str, chunk: str) -> Optional[str]:
        """Try to fix a Discord link using message metadata from the chunk."""
        try:
            # Find the message ID and channel ID in the chunk
            message_match = re.search(r'Message ID: (\d+)', chunk)
            channel_match = re.search(r'Channel ID: (\d+)', chunk)
            
            if message_match and channel_match:
                message_id = message_match.group(1)
                channel_id = channel_match.group(1)
                
                # Create the correct Discord link
                correct_link = f"https://discord.com/channels/{self.SERVER_ID}/{channel_id}/{message_id}"
                
                # Replace the incorrect link in the content
                fixed_content = re.sub(
                    r'\(https://discord\.com/channels/[^)]+\)',
                    f'({correct_link})',
                    content
                )
                
                return fixed_content
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error fixing Discord link: {e}")
            return None

    def _validate_bullet_verbose(self, bullet: BulletPoint) -> str:
        """Return detailed validation results for logging."""
        result = []
        
        if bullet.content.strip().startswith('-'):
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

        return ' | '.join(result)

    def _post_process_bullets(self, bullets: List[str]) -> List[str]:
        """Post-process bullets to merge related updates."""
        self.logger.info("\n" + "="*80)
        self.logger.info("Post-processing Bullets")
        self.logger.info("="*80)

        # Group bullets by project
        project_bullets = {}
        other_bullets = []
        
        for bullet in bullets:
            project_match = re.search(r'\*\*([^*]+)\*\*', bullet)
            if project_match:
                project_name = project_match.group(1).strip()
                if project_name not in project_bullets:
                    project_bullets[project_name] = [bullet]
                else:
                    project_bullets[project_name].append(bullet)
            else:
                other_bullets.append(bullet)

        # Log project statistics
        self.logger.info("\n📊 Project Statistics:")
        self.logger.info(f"   Projects found: {len(project_bullets)}")
        self.logger.info(f"   Other bullets: {len(other_bullets)}")
        
        for project, bullet_list in project_bullets.items():
            self.logger.info(f"   - {project}: {len(bullet_list)} updates")

        # Prepare final bullet list
        processed_bullets = []
        for project_bullet_list in project_bullets.values():
            processed_bullets.extend(project_bullet_list)
        processed_bullets.extend(other_bullets)
        
        # Handle category replacement
        final_bullets = [
            bullet.replace(
                "### Insightful/Philosophical Community Discussions",
                "### Development Updates"
            )
            if "Core Features" in bullet else bullet
            for bullet in processed_bullets
        ]

        self.logger.info(f"\n✅ Post-processing complete - Final bullet count: {len(final_bullets)}")
        self.logger.info("="*80 + "\n")
        
        return final_bullets
