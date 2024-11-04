"""Clean and standardize text content."""
import re
from typing import List

class TextCleaner:
    """Handles text cleaning and standardization operations."""
    
    @staticmethod
    def clean_bot_references(text: str) -> str:
        """Clean up bot references in text."""
        return re.sub(
            r"(?:Bot|GroupAnonymousBot)\s+(?:highlighted|mentioned|discussed|shared|announced)",
            "The team announced",
            text
        )
    
    @staticmethod
    def remove_common_suffixes(text: str) -> str:
        """Remove common suffixes from text."""
        return re.sub(
            r'\s+(?:implementation|update|development|improvements?|remarks|protocol|v\d+|version\s+\d+|integration)s?\s*$',
            '',
            text.lower()
        )
    
    @staticmethod
    def clean_markdown_links(text: str) -> str:
        """Remove markdown links while preserving text."""
        return re.sub(r'\[(?:here|[^\]]+)\]\([^)]+\)', '', text)
    
    @staticmethod
    def extract_content_without_formatting(text: str) -> str:
        """Extract plain content without markdown formatting."""
        # Remove project name formatting
        text = re.sub(r'\*\*[^*]+\*\*:', '', text)
        # Remove markdown links
        text = TextCleaner.clean_markdown_links(text)
        return text.strip()
    
    @staticmethod
    def standardize_whitespace(text: str) -> str:
        """Standardize whitespace in text."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        return text.strip()
