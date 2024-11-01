# services/bullet_processor.py
import re
import logging
from openai import OpenAI
from typing import List
from utils.prompts import SummaryPrompts

class BulletProcessor:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self.MAX_RETRIES = 7
        self.MIN_BULLETS_PER_CHUNK = 40
        self.MAX_TOKENS = 8000  # Leave some buffer for the response
        self.seen_projects = set()
        self.ACTION_VERBS = [
            "discussed", "shared", "announced", "implemented", "updated",
            "added", "fixed", "completed", "noted", "mentioned", "explained",
            "developed", "created", "built", "launched", "deployed", "merged",
            "tested", "configured", "optimized", "refactored", "designed",
            "integrated", "released", "improved", "started", "proposed",
            "initiated", "showcased", "demonstrated", "published", "documented",
            "analyzed", "evaluated", "reviewed", "submitted", "prepared",
            "enabled", "established", "introduced", "suggested", "recommended"
        ]

    def process_chunks(self, chunks: List[str]) -> List[str]:
        collected_bullets = []
        self.seen_projects = set()  # Reset seen projects for new processing
        
        for i, chunk in enumerate(chunks):
            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            self.logger.info(f"{'='*50}")
            
            try:
                # Split chunk if it's too large
                sub_chunks = self._split_chunk_by_tokens(chunk)
                for sub_chunk in sub_chunks:
                    chunk_bullets = self._process_single_chunk(sub_chunk)
                    if chunk_bullets:  # Only extend if we got valid bullets
                        collected_bullets.extend(chunk_bullets)
            except Exception as e:
                self.logger.error(f"Error processing chunk {i+1}: {e}", exc_info=True)
                continue  # Continue with next chunk even if this one fails
            
        self.logger.info(f"\nTotal bullets collected: {len(collected_bullets)}")
        
        if not collected_bullets:
            raise ValueError("No valid bullets were generated from any chunks")
            
        # Post-process bullets to merge related project updates and ensure proper categorization
        collected_bullets = self._post_process_bullets(collected_bullets)
            
        return collected_bullets

    def _split_chunk_by_tokens(self, chunk: str) -> List[str]:
        """Split a chunk into smaller pieces if it exceeds token limit."""
        # Rough estimation: 1 token ≈ 4 characters
        char_limit = self.MAX_TOKENS * 4
        
        if len(chunk) <= char_limit:
            return [chunk]
            
        # Split by newlines first to maintain message integrity
        lines = chunk.split('\n')
        current_chunk = []
        chunks = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            if current_length + line_length > char_limit:
                if current_chunk:  # Save current chunk if it exists
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
                
        if current_chunk:  # Add the last chunk
            chunks.append('\n'.join(current_chunk))
            
        return chunks

    def _process_single_chunk(self, chunk: str) -> List[str]:
        chunk_bullets = []
        retry_count = 0
        consecutive_no_new = 0
        
        while retry_count < self.MAX_RETRIES:
            try:
                print(f"\nAttempt {retry_count + 1}:")
                print("-" * 30)
                
                new_bullets = self._extract_bullets_from_chunk(chunk, retry_count, len(chunk_bullets))
                if not new_bullets:  # Validate we got bullets from the API
                    raise ValueError("No bullets returned from API")
                    
                print(f"\nFound {len(new_bullets)} raw bullets:")
                for i, bullet in enumerate(new_bullets, 1):
                    print(f"\nBullet {i}:")
                    print(bullet)
                    validation_result = self._validate_bullet_verbose(bullet)
                    print(f"Validation: {validation_result}")
                    
                valid_new_bullets = [
                    bullet for bullet in new_bullets
                    if self._is_valid_bullet(bullet)
                ]
                
                print(f"\nValid new bullets: {len(valid_new_bullets)}/{len(new_bullets)}")
                print("Valid bullets being added:")
                for bullet in valid_new_bullets:
                    print(f"✓ {bullet}")
                
                if valid_new_bullets:
                    chunk_bullets.extend(valid_new_bullets)
                    consecutive_no_new = 0
                else:
                    consecutive_no_new += 1
                    print(f"No new valid bullets found in attempt {retry_count + 1}")
                
                if len(chunk_bullets) >= self.MIN_BULLETS_PER_CHUNK or consecutive_no_new >= 3:
                    break
                    
                retry_count += 1
                
            except Exception as e:
                self.logger.error(f"Error in attempt {retry_count + 1}: {e}", exc_info=True)
                retry_count += 1
                if retry_count >= self.MAX_RETRIES:
                    if not chunk_bullets:  # If we have no bullets at all, raise the error
                        raise ValueError(f"Failed to generate any valid bullets after {self.MAX_RETRIES} attempts")
                    break  # Otherwise, return what we have
        
        return chunk_bullets

    def _extract_bullets_from_chunk(self, chunk: str, retry_count: int, current_bullets: int) -> List[str]:
        temperature = 0.7 + (retry_count * 0.05)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SummaryPrompts.get_system_prompt()},
                    {"role": "user", "content": SummaryPrompts.get_user_prompt(chunk, current_bullets)}
                ],
                temperature=min(temperature, 0.95),
                max_tokens=2000
            )
            
            # Access the content directly from the response
            summary = response.choices[0].message.content
            bullets = [b.strip() for b in summary.split('\n') if b.strip().startswith('-')]
            
            if not bullets:
                raise ValueError("API response contained no bullet points")
                
            return bullets
            
        except Exception as e:
            self.logger.error(f"Error in API call: {e}", exc_info=True)
            raise

    def _is_valid_bullet(self, bullet: str) -> bool:
        """Validate bullet point format focusing on essential requirements."""
        if not bullet.strip().startswith('-'):
            return False

        # Must have Discord link
        has_discord_link = bool(re.search(r'\(https://discord\.com/channels/[^)]+\)', bullet))
        if not has_discord_link:
            return False

        # Should have some technical content (minimum length)
        if len(bullet.strip()) <= 50:
            return False

        # Extract project name if present
        project_match = re.search(r'\*\*([^*]+)\*\*', bullet)
        if project_match:
            project_name = project_match.group(1).strip()
            # Skip if we've seen this project before
            if project_name in self.seen_projects:
                return False
            self.seen_projects.add(project_name)

        return True

    def _validate_bullet_verbose(self, bullet: str) -> str:
        """Validate bullet point and return detailed explanation."""
        result = []
        
        # Basic structure check
        if not bullet.strip().startswith('-'):
            result.append("❌ Does not start with '-'")
        else:
            result.append("✓ Starts with '-'")

        # Check for Discord link
        if re.search(r'\(https://discord\.com/channels/[^)]+\)', bullet):
            result.append("✓ Has Discord link")
        else:
            result.append("❌ Missing Discord link")

        # Check length
        length = len(bullet.strip())
        if length > 50:
            result.append(f"✓ Length ok: {length} chars")
        else:
            result.append(f"❌ Too short: {length} chars")

        # Check for project duplication
        project_match = re.search(r'\*\*([^*]+)\*\*', bullet)
        if project_match:
            project_name = project_match.group(1).strip()
            if project_name in self.seen_projects:
                result.append("❌ Duplicate project")
            else:
                result.append("✓ New project")

        return ' | '.join(result)

    def _post_process_bullets(self, bullets: List[str]) -> List[str]:
        """Post-process bullets to merge related updates and ensure proper categorization."""
        # Group bullets by project
        project_bullets = {}
        other_bullets = []
        
        for bullet in bullets:
            project_match = re.search(r'\*\*([^*]+)\*\*', bullet)
            if project_match:
                project_name = project_match.group(1).strip()
                if project_name not in project_bullets:
                    project_bullets[project_name] = bullet
                else:
                    # Merge information if it's not redundant
                    existing_info = project_bullets[project_name]
                    new_info = bullet[bullet.find(':')+1:].strip()
                    if new_info not in existing_info:
                        project_bullets[project_name] = f"{existing_info} {new_info}"
            else:
                other_bullets.append(bullet)
        
        # Combine processed bullets
        processed_bullets = list(project_bullets.values()) + other_bullets
        
        # Ensure Core Features discussion is under Development Updates
        processed_bullets = [
            bullet.replace("### Insightful/Philosophical Community Discussions", "### Development Updates")
            if "Core Features" in bullet
            else bullet
            for bullet in processed_bullets
        ]
        
        return processed_bullets
