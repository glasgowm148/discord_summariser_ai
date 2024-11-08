"""Update deduplication utilities."""
import re
from typing import List
from difflib import SequenceMatcher

from helpers.processors.text_processor import TextProcessor


class UpdateDeduplicator:
    """Handles deduplication of updates with advanced logic."""

    def __init__(self, text_processor: TextProcessor):
        """
        Initialize the deduplicator with a text processor.
        
        :param text_processor: Processor for text-related operations
        """
        self.text_processor = text_processor

    def deduplicate_updates(self, updates: List[str]) -> List[str]:
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
