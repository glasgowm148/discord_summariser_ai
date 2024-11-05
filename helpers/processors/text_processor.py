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
        
        # Minimal removal of common phrases with more precise whitespace handling
        content = re.sub(
            r'(?i)\s*(read more|explore|view|catch|delve|find out|check out|discover)\s*(?:more)?\s*',
            ' ',
            content
        )
        
        # Normalize whitespace more comprehensively
        return re.sub(r'\s+', ' ', content).strip()

    def optimize_chunk_size(self, chunk: str, max_length: int = 4000) -> str:
        """
        Optimize chunk size for processing, similar to the previous implementation.
        If chunk is too long, extract core content.
        """
        # If chunk is already within acceptable length, return as is
        if len(chunk) <= max_length:
            return chunk
        
        # Try to extract core content
        optimized_chunk = self.extract_core_content(chunk)
        
        # If optimization didn't help, truncate
        return optimized_chunk[:max_length]

    @staticmethod
    def extract_discord_url(text: str) -> Optional[str]:
        """
        Extract Discord URL from text with more robust validation.
        Handles various Discord link formats and ensures basic structure.
        """
        # Regex to match Discord channel/message links with more flexibility
        discord_url_pattern = r'https://discord\.com/channels/(\d+)/(\d+)/(\d+)'
        match = re.search(discord_url_pattern, text)
        
        if match:
            # Validate server, channel, and message IDs
            server_id, channel_id, message_id = match.groups()
            
            # Basic validation: ensure all IDs are numeric and non-zero
            if (server_id.isdigit() and channel_id.isdigit() and message_id.isdigit() and
                int(server_id) > 0 and int(channel_id) > 0 and int(message_id) > 0):
                return match.group(0)
        
        return None

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

    def simplify_project_name(self, project_name: str) -> str:
        """
        Simplify project name by removing common words and standardizing.
        
        This method is referenced in the bullet_processor, so I'll add a basic implementation.
        """
        # Remove common words and standardize
        simplified = re.sub(r'(?i)\b(the|a|an|project|protocol|platform)\b', '', project_name).strip()
        return simplified.title()

    @staticmethod
    def is_meta_commentary(text: str) -> bool:
        """Check if text is meta-commentary."""
        return bool(re.search(
            r'(?i)(these updates cover|this discussion highlights|for more|further details|'
            r'provide valuable insights|reflecting both|ongoing discussions and developments|'
            r'community engagement|technical intricacies)',
            text
        ))

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """
        Clean excess whitespace while preserving markdown formatting.
        Handles multiple scenarios to ensure clean, consistent formatting.
        """
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        # Rejoin lines with consistent double newline
        return '\n\n'.join(lines)

    def standardize_text(self, text: str) -> str:
        """
        Standardize text by cleaning whitespace and preserving markdown.
        
        This method is referenced in the bullet_processor, so I'll add a basic implementation.
        """
        # Preserve markdown formatting while removing extra whitespace
        # Split into lines to handle markdown elements separately
        lines = text.split('\n')
        
        # Clean each line
        cleaned_lines = []
        for line in lines:
            # Remove leading/trailing whitespace
            line = line.strip()
            
            # For bullet points, ensure single space after bullet
            if line.startswith('- '):
                line = '- ' + line[2:].strip()
            
            # For headers, ensure single space after header marker
            if re.match(r'^#+\s', line):
                line = re.sub(r'^(#+)\s+', r'\1 ', line)
            
            if line:
                cleaned_lines.append(line)
        
        # Rejoin with consistent newlines
        return '\n'.join(cleaned_lines)
