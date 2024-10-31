# services/summary_finalizer.py
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, List
import logging
from openai import OpenAI
from utils.prompts import SummaryPrompts

class SummaryFinalizer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)

    def create_final_summary(self, bullets: List[str], days_covered: int) -> Tuple[Optional[str], Optional[str]]:
        """Create the final categorized summary."""
        try:
            # Log original bullets
            self.logger.info("\nOriginal bullets before final summary:")
            for i, bullet in enumerate(bullets, 1):
                self.logger.info(f"{i}. {bullet}")

            # Compare bullets and remove duplicates while preserving technical details
            unique_bullets = self._remove_duplicate_bullets(bullets)
            
            if len(unique_bullets) != len(bullets):
                self.logger.info(f"\nRemoved {len(bullets) - len(unique_bullets)} duplicate bullets")
                self.logger.info("Unique bullets after deduplication:")
                for i, bullet in enumerate(unique_bullets, 1):
                    self.logger.info(f"{i}. {bullet}")

            # Make up to 3 attempts to get a valid summary
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    final_response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{
                            "role": "user", 
                            "content": SummaryPrompts.get_final_summary_prompt(unique_bullets, days_covered)
                        }],
                        temperature=0.6,
                        max_tokens=2000
                    )

                    summary_content = final_response.model_dump()["choices"][0]["message"]["content"]
                    
                    # Validate the summary contains bullet points
                    if not any(line.strip().startswith('-') for line in summary_content.split('\n')):
                        raise ValueError("Generated summary contains no bullet points")
                    
                    final_summary = self._clean_final_summary(summary_content)
                    
                    # Additional validation of cleaned summary
                    final_bullets = [line for line in final_summary.split('\n') if line.strip().startswith('-')]
                    if not final_bullets:
                        raise ValueError("Cleaned summary contains no bullet points")
                    
                    # Log the final bullets for comparison
                    self.logger.info("\nFinal summary bullets:")
                    for i, bullet in enumerate(final_bullets, 1):
                        self.logger.info(f"{i}. {bullet}")
                    
                    self.logger.info(f"\nBullets processed from {len(bullets)} to {len(final_bullets)}")
                    
                    self._log_summary(final_summary)
                    
                    summary_with_cta = self._add_call_to_action(final_summary)
                    return final_summary, summary_with_cta
                    
                except ValueError as ve:
                    self.logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {str(ve)}")
                    if attempt == max_attempts - 1:
                        raise
                except Exception as e:
                    self.logger.error(f"Attempt {attempt + 1}/{max_attempts} failed with unexpected error: {str(e)}")
                    if attempt == max_attempts - 1:
                        raise
            
        except Exception as e:
            self.logger.error(f"Error creating final summary: {str(e)}", exc_info=True)
            return None, None

    def _remove_duplicate_bullets(self, bullets: List[str]) -> List[str]:
        """Remove duplicate bullets while preserving the most detailed version."""
        seen_content = {}
        unique_bullets = []
        
        for bullet in bullets:
            # Extract core content without emoji and formatting
            core_content = re.sub(r'🔧|🚀|📊|🔗|🔐|🌐|📦|🔄|🔒', '', bullet)
            core_content = re.sub(r'\[.*?\]\(.*?\)', '', core_content)
            core_content = re.sub(r'\*\*.*?\*\*', '', core_content)
            core_content = core_content.lower().strip()
            
            # If we haven't seen this content, or this version is more detailed
            if core_content not in seen_content or len(bullet) > len(seen_content[core_content]):
                seen_content[core_content] = bullet
        
        return list(seen_content.values())

    def _clean_final_summary(self, summary: str) -> str:
        """Clean and validate the final summary."""
        # Remove any notes or comments
        summary = re.sub(r'\(Note:.*?\)', '', summary, flags=re.DOTALL)
        summary = re.sub(r'\n\s*\n', '\n', summary)
        
        # Process each line
        valid_sections = []
        for line in summary.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('#') or line.startswith('-'):
                valid_sections.append(line)
            else:
                # For non-header, non-bullet lines, check if they're part of the content
                if len(line) > 10:  # Arbitrary minimum length for content
                    valid_sections.append(line)
        
        cleaned_summary = '\n'.join(valid_sections)
        
        # Validate the cleaned summary has content
        if not cleaned_summary.strip():
            raise ValueError("Cleaning resulted in empty summary")
            
        return cleaned_summary

    def _log_summary(self, summary: str) -> None:
        """Log the generated summary."""
        log_file = Path('sent_summaries.md')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n# {timestamp}\n{summary}\n{'#' * 80}\n")
        except Exception as e:
            self.logger.error(f"Failed to log summary: {e}")

    def _add_call_to_action(self, summary: str) -> str:
        """Add call to action to the summary."""
        discord_invite = os.getenv('DISCORD_INVITE_LINK', 'https://discord.gg/ergo')
        return f"{summary}\n\nJoin the discussion on Discord: {discord_invite}"
