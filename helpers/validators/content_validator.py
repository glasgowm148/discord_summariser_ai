"""Content validation utilities."""

import re
from typing import List, Set, Tuple
from helpers.processors.text_processor import TextProcessor


class ContentValidator:
    @staticmethod
    def remove_duplicate_updates(updates: List[str]) -> List[str]:
        """Remove duplicate updates while preserving the most informative version."""
        unique_updates = []
        processed_contents = []
        seen_urls: Set[str] = set()

        for update in updates:
            # Skip meta-commentary
            if TextProcessor.is_meta_commentary(update):
                continue
                
            core_content = TextProcessor.extract_core_content(update)
            discord_url = TextProcessor.extract_discord_url(update)
            
            # Skip if empty after processing
            if not core_content:
                continue
            
            # Skip if URL already seen
            if discord_url and discord_url in seen_urls:
                continue
                
            # Check if we have a similar update
            is_duplicate = False
            for idx, existing_content in enumerate(processed_contents):
                if TextProcessor.are_similar(core_content, existing_content):
                    # If this version is more informative, replace the existing one
                    if TextProcessor.get_info_score(update) > TextProcessor.get_info_score(unique_updates[idx]):
                        # Remove old URL from seen_urls if it exists
                        old_url = TextProcessor.extract_discord_url(unique_updates[idx])
                        if old_url:
                            seen_urls.remove(old_url)
                        # Add new update and URL
                        unique_updates[idx] = update
                        if discord_url:
                            seen_urls.add(discord_url)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_updates.append(update)
                processed_contents.append(core_content)
                if discord_url:
                    seen_urls.add(discord_url)

        return unique_updates

    @staticmethod
    def validate_and_clean_summary(summary: str) -> Tuple[str, bool]:
        """Validate and clean summary content."""
        if not summary:
            return "", False
            
        lines = summary.split('\n')
        valid_lines = []
        in_bullet_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Keep headers
            if line.startswith('#'):
                valid_lines.append(line)
                in_bullet_section = True
                continue
                
            # Skip meta-commentary unless it's a footer
            if TextProcessor.is_meta_commentary(line) and not line.startswith('*This summary'):
                continue
                
            # Only keep bullet points in bullet sections
            if in_bullet_section:
                if line.startswith('-'):
                    valid_lines.append(line)
                # Skip any non-bullet point lines in bullet sections
                continue
            else:
                # Keep non-bullet section content (like headers)
                valid_lines.append(line)
                
        cleaned_content = '\n\n'.join(valid_lines)
        return cleaned_content, bool(cleaned_content.strip())

    @staticmethod
    def validate_categories(updates: List[str]) -> List[str]:
        """Validate and standardize update categories."""
        validated_updates = []
        
        for update in updates:
            # Extract category if present
            category_match = TextProcessor.extract_category(update)
            if not category_match:
                # If no category, try to extract the first significant term as category
                # Remove any bullet point and emoji if present
                clean_update = re.sub(r'^- [^\w\s]?\s*', '', update)
                
                # Extract first significant word or phrase
                words = clean_update.split()
                if words:
                    # Use first word that's not a common word as category
                    for word in words:
                        if len(word) > 2 and not word.lower() in {'the', 'and', 'but', 'for', 'with', 'has', 'was', 'are'}:
                            update = f"- **{word}**: {clean_update}"
                            break
                    else:
                        # If no suitable word found, just keep original update
                        update = f"- {clean_update}"
            
            validated_updates.append(update)
            
        return validated_updates
