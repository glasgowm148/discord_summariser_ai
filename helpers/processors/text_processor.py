"""Text processing utilities for cleaning and extracting content."""

import re
from typing import Optional, Match
from difflib import SequenceMatcher


class TextProcessor:
    @staticmethod
    def extract_core_content(text: str) -> str:
        """Extract core content with minimal formatting removal."""
        # Preserve more of the original context
        content = text.strip()
        
        # Minimal link removal
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        
        # Preserve project names and some formatting
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        
        # Minimal removal of common phrases
        content = re.sub(
            r'(?i)(read more|explore|view|catch|delve|find out|check out|discover)\s*(?:more\s*)?',
            '',
            content
        )
        
        # Normalize whitespace, but keep some original structure
        return ' '.join(content.split())

    @staticmethod
    def extract_discord_url(text: str) -> Optional[str]:
        """Extract Discord URL from text."""
        match = re.search(r'https://discord\.com/channels/\d+/\d+/\d+', text)
        return match.group(0) if match else None

    @staticmethod
    def extract_category(text: str) -> Optional[Match[str]]:
        """Extract category from text."""
        # Look for category in bold followed by colon
        category_match = re.search(r'\*\*(.*?)\*\*:', text)
        return category_match

    @staticmethod
    def are_similar(text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar using sequence matcher, with a lower threshold."""
        # Preserve more context by using a lower similarity threshold
        return SequenceMatcher(None, text1, text2).ratio() > threshold

    @staticmethod
    def get_info_score(text: str) -> int:
        """Calculate an information score for text based on various factors."""
        # More nuanced scoring to preserve unique information
        word_count = len(text.split())
        
        # Presence of specific details increases score
        has_numbers = 2 if re.search(r'\d', text) else 0
        has_quotes = 3 if '"' in text or "'" in text else 0
        has_technical_terms = 3 if re.search(
            r'(?i)(implementation|development|infrastructure|protocol|system|platform|version|strategy)',
            text
        ) else 0
        
        # Bonus for unique project mentions
        has_unique_project = 2 if re.search(r'\*\*[A-Z]', text) else 0
        
        return word_count + has_numbers + has_quotes + has_technical_terms + has_unique_project

    @staticmethod
    def is_meta_commentary(text: str) -> bool:
        """Check if text is meta-commentary."""
        return bool(re.search(
            r'(?i)(these updates cover|this discussion highlights|for more|further details)',
            text
        ))

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Clean excess whitespace while preserving markdown formatting."""
        return re.sub(r'\n\s*\n\s*\n', '\n\n', text)
