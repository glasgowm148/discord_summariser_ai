"""Content validation utilities."""

import re
import logging
from typing import List, Set, Tuple, Optional
from helpers.processors.text_processor import TextProcessor


class ContentValidator:
    @staticmethod
    def remove_duplicate_updates(updates: List[str], channel_name: Optional[str] = None) -> List[str]:
        """
        Remove duplicate updates with advanced filtering.
        
        Considers:
        - Core content similarity
        - Information richness
        - Ecosystem relevance
        - Optional channel name filtering
        """
        unique_updates = []
        processed_contents = []
        seen_urls: Set[str] = set()
        seen_topics: Set[str] = set()
        seen_channels: Set[str] = set()

        for update in updates:
            # Skip meta-commentary and personal complaints
            if (TextProcessor.is_meta_commentary(update) or 
                ContentValidator._is_personal_complaint(update)):
                continue
                
            core_content = TextProcessor.extract_core_content(update)
            discord_url = TextProcessor.extract_discord_url(update)
            
            # Skip if empty after processing
            if not core_content:
                continue
            
            # Skip if URL already seen
            if discord_url and discord_url in seen_urls:
                continue
            
            # Extract topic/category and channel
            topic = ContentValidator._extract_update_topic(update)
            current_channel = ContentValidator._extract_channel(update)
            
            # Optional channel name filtering
            if channel_name and current_channel and current_channel.lower() != channel_name.lower():
                continue
            
            # More aggressive duplicate detection
            is_duplicate = False
            for idx, existing_content in enumerate(processed_contents):
                # Check for very high similarity
                similarity_ratio = TextProcessor.calculate_similarity(core_content, existing_content)
                
                # If updates are extremely similar and share the same topic
                if similarity_ratio > 0.8:
                    # If this version is more informative, replace the existing one
                    if (TextProcessor.get_info_score(update) > 
                        TextProcessor.get_info_score(unique_updates[idx])):
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
            
            # Additional check for topic-based duplicates
            if topic and topic in seen_topics:
                is_duplicate = True
            
            if not is_duplicate:
                unique_updates.append(update)
                processed_contents.append(core_content)
                if discord_url:
                    seen_urls.add(discord_url)
                if topic:
                    seen_topics.add(topic)
                if current_channel:
                    seen_channels.add(current_channel)

        return unique_updates

    @staticmethod
    def _extract_channel(update: str) -> Optional[str]:
        """
        Extract the channel name from an update.
        
        Looks for channel name indicators in the update text.
        """
        # Extract channel ID from Discord URL
        url_match = re.search(r'discord\.com/channels/\d+/(\d+)/\d+', update)
        if url_match:
            channel_id = url_match.group(1)
            logging.info(f"   📍 Channel ID: {channel_id}")
            return channel_id
            
        # Common channel name extraction patterns
        channel_patterns = [
            r'#(\w+)',  # Discord channel format
            r'in (\w+) channel',  # Descriptive format
            r'from (\w+) channel',  # Alternative descriptive format
        ]
        
        for pattern in channel_patterns:
            match = re.search(pattern, update, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    @staticmethod
    def validate_and_clean_summary(summary: str) -> Tuple[str, bool]:
        """Validate and clean summary content."""
        if not summary:
            return "", False
            
        lines = summary.split('\n')
        valid_lines = []
        in_bullet_section = False
        channel_name = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Extract channel name from Discord link if not already found
            if not channel_name:
                channel_match = re.search(r'discord\.com/channels/\d+/(\d+)/\d+', line)
                if channel_match:
                    channel_name = channel_match.group(1)
                
                # Try to extract hashtag channel name
                hashtag_match = re.search(r'#(\w+)', line)
                if hashtag_match:
                    channel_name = hashtag_match.group(1)
            
            # Keep headers
            if line.startswith('#'):
                valid_lines.append(line)
                in_bullet_section = True
                continue
                
            # Skip meta-commentary unless it's a footer
            if (TextProcessor.is_meta_commentary(line) and 
                not line.startswith('*This summary')):
                continue
                
            # Only keep bullet points in bullet sections
            if in_bullet_section:
                if line.startswith('-'):
                    # Additional filtering to remove personal updates
                    if not ContentValidator._is_personal_complaint(line):
                        # Log the channel name for each valid bullet point
                        if channel_name:
                            logging.info(f"   📍 Channel: {channel_name}")
                        
                        # Prepend channel name if found
                        if channel_name:
                            line = f"[{channel_name}] {line}"
                        valid_lines.append(line)
                # Skip any non-bullet point lines in bullet sections
                continue
            else:
                # Keep non-bullet section content (like headers)
                valid_lines.append(line)
                
        cleaned_content = '\n\n'.join(valid_lines)
        return cleaned_content, bool(cleaned_content.strip())

    @staticmethod
    def _is_personal_complaint(update: str) -> bool:
        """
        Detect if an update is a personal complaint or non-ecosystem update.
        
        Looks for indicators of personal or trivial content.
        """
        # List of keywords and phrases indicating personal or non-ecosystem updates
        personal_indicators = [
            'video editing', 'personal challenge', 'workflow issue', 
            'having trouble', 'difficult to manage', 'struggling with',
            'my experience', 'individual perspective', 'personal note',
            'appreciate the welcome', 'warm welcome', 'new member',
            'just joined', 'feeling welcomed', 'community atmosphere'
        ]
        
        # Convert update to lowercase for case-insensitive matching
        lower_update = update.lower()
        
        # Check for personal indicators
        return any(indicator in lower_update for indicator in personal_indicators)

    @staticmethod
    def _extract_update_topic(update: str) -> str:
        """
        Extract a standardized topic from an update.
        
        Focuses on key ecosystem-related terms.
        """
        # Extract category or project name
        category_match = TextProcessor.extract_category(update)
        if category_match:
            return category_match.group(1).strip().lower()
        
        # Fallback to extracting key terms
        key_terms = [
            'stablecoin', 'mining', 'market', 'token', 'blockchain', 
            'cryptocurrency', 'regulation', 'liquidity', 'protocol'
        ]
        
        lower_update = update.lower()
        for term in key_terms:
            if term in lower_update:
                return term
        
        return ''

    @staticmethod
    def validate_categories(updates: List[str], channel_name: Optional[str] = None) -> List[str]:
        """
        Validate and standardize update categories.
        
        Optional channel name filtering.
        """
        validated_updates = []
        
        for update in updates:
            # Skip personal complaints
            if ContentValidator._is_personal_complaint(update):
                continue
            
            # Optional channel name filtering
            current_channel = ContentValidator._extract_channel(update)
            if channel_name and current_channel and current_channel.lower() != channel_name.lower():
                continue
            
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
                        if (len(word) > 2 and 
                            not word.lower() in {'the', 'and', 'but', 'for', 'with', 'has', 'was', 'are'}):
                            update = f"- **{word}**: {clean_update}"
                            break
                    else:
                        # If no suitable word found, just keep original update
                        update = f"- {clean_update}"
            
            # Add channel name to the update if extracted
            if current_channel:
                update = f"[{current_channel}] {update}"
            
            validated_updates.append(update)
            
        return validated_updates
