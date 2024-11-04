"""Core content formatting utilities."""

import re
from typing import List


class ContentFormatter:
    @staticmethod
    def format_bullet_point(text: str) -> str:
        """Format text as a bullet point with emoji."""
        text = text.strip()
        
        # Add bullet point if not present
        if not text.startswith('-'):
            text = f"- {text}"
            
        # Add emoji if not present after bullet point
        if not re.match(r'^- [^\w\s]', text):
            text = re.sub(r'^- ', '- 📢 ', text)
            
        return text

    @staticmethod
    def format_discord_summary(header: str, updates: List[str]) -> str:
        """Format the complete Discord summary."""
        formatted_updates = [ContentFormatter.format_bullet_point(update) for update in updates]
        return f"{header}\n" + "\n".join(formatted_updates)

    @staticmethod
    def format_project_name(name: str) -> str:
        """Format project name with bold markdown."""
        if not name.startswith('**'):
            name = f"**{name}**"
        return name

    @staticmethod
    def format_discord_link(text: str, url: str) -> str:
        """Format Discord link with markdown."""
        return f"[{text}]({url})"

    @staticmethod
    def add_call_to_action(text: str) -> str:
        """Add Discord call to action to text."""
        return f"{text}\n\nJoin the discussion on Discord: https://discord.gg/ergo-platform-668903786361651200"

    @staticmethod
    def format_header(text: str, level: int = 2) -> str:
        """Format text as markdown header."""
        return f"{'#' * level} {text}"

    @staticmethod
    def format_footer(text: str) -> str:
        """Format text as footer with separator."""
        return f"\n\n---\n{text}"

    @staticmethod
    def clean_formatting(text: str) -> str:
        """Clean up text formatting."""
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Ensure consistent spacing after bullet points
        text = re.sub(r'- +', '- ', text)
        
        # Ensure proper spacing around links
        text = re.sub(r'\]\s*\(', '](', text)
        
        # Remove trailing whitespace from each line
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        
        # Ensure proper spacing around headers
        text = re.sub(r'\n#+\s*', '\n\n#', text)
        text = re.sub(r'\n\n\n#+', '\n\n#', text)
        
        # Remove empty bullet points
        text = re.sub(r'- \s*\n', '', text)
        
        # Ensure proper spacing after colons in bullet points
        text = re.sub(r':\s+', ': ', text)
        
        return text.strip()
