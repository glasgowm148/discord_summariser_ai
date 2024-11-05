"""Platform-specific formatting for social media."""

import logging
import re
from typing import List, Optional

from helpers.formatters.content_formatter import ContentFormatter


class SocialMediaFormatter:
    @staticmethod
    def format_for_platform(content: str, platform: str) -> str:
        """
        Format content for a specific social media platform.
        
        Args:
            content (str): The content to be formatted
            platform (str): Target social media platform
        
        Returns:
            str: Formatted content for the specified platform
        
        Raises:
            ValueError: If an unsupported platform is specified
        """
        try:
            # Normalize platform name
            platform = platform.lower().strip()
            
            # Mapping of platforms to their formatting methods
            formatters = {
                'twitter': SocialMediaFormatter.format_for_twitter,
                'facebook': SocialMediaFormatter.format_for_facebook,
                'instagram': SocialMediaFormatter.format_for_instagram,
                'linkedin': SocialMediaFormatter.format_for_linkedin,
                'reddit': SocialMediaFormatter.format_for_reddit
            }
            
            # Select formatter or raise error
            formatter = formatters.get(platform)
            if not formatter:
                raise ValueError(f"Unsupported platform: {platform}")
            
            return formatter(content)
        
        except Exception as e:
            logging.error(f"Error formatting for {platform}: {e}")
            return content  # Fallback to original content

    @staticmethod
    def _preprocess_content(content: str) -> List[str]:
        """
        Preprocess content by cleaning and splitting into lines.
        
        Args:
            content (str): Raw content to preprocess
        
        Returns:
            List[str]: Cleaned and processed lines
        """
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Remove markdown headers
            if line.startswith('#'):
                line = line.lstrip('#').strip()
            
            # Clean and format bullet points
            line = ContentFormatter.format_bullet_point(line)
            processed_lines.append(line)
        
        return processed_lines

    @staticmethod
    def format_for_twitter(content: str) -> str:
        """Format content for Twitter with character limit and hashtags."""
        processed_lines = SocialMediaFormatter._preprocess_content(content)
        formatted_content = '\n'.join(processed_lines).strip()
        
        # Twitter character limit
        max_chars = 280
        hashtags = " #Ergo #Blockchain #CryptoUpdates"
        
        # Truncate if too long
        if len(formatted_content) + len(hashtags) > max_chars:
            formatted_content = formatted_content[:max_chars - len(hashtags) - 3] + "..."
        
        return formatted_content + hashtags

    @staticmethod
    def format_for_facebook(content: str) -> str:
        """Format content for Facebook with engagement-friendly formatting."""
        processed_lines = SocialMediaFormatter._preprocess_content(content)
        
        # Add emojis and formatting
        formatted_lines = ['📢 Ergo Platform Update 🚀']
        formatted_lines.extend(processed_lines)
        
        # Add call to action
        formatted_lines.append("\n🔗 Join our community: https://discord.gg/ergo-platform")
        
        return '\n'.join(formatted_lines)

    @staticmethod
    def format_for_instagram(content: str) -> str:
        """Format content for Instagram with visual-friendly formatting."""
        processed_lines = SocialMediaFormatter._preprocess_content(content)
        
        # Add visual markers and split content
        formatted_lines = ['🚀 Ergo Platform Update 🌐']
        formatted_lines.extend(processed_lines)
        
        # Add hashtags
        hashtags = (
            "\n\n#Ergo #Blockchain #CryptoTech #DecentralizedFinance "
            "#CryptoInnovation #BlockchainDevelopment #Cryptocurrency"
        )
        
        return '\n'.join(formatted_lines) + hashtags

    @staticmethod
    def format_for_linkedin(content: str) -> str:
        """Format content for LinkedIn with professional tone."""
        processed_lines = SocialMediaFormatter._preprocess_content(content)
        
        # Professional header
        formatted_lines = ['🏢 Ergo Platform Technical Update']
        formatted_lines.extend(processed_lines)
        
        # Professional call to action
        formatted_lines.append(
            "\nStay informed about cutting-edge blockchain technology. "
            "Connect with our community for deeper insights."
        )
        
        return '\n'.join(formatted_lines)

    @staticmethod
    def format_for_reddit(content: str) -> str:
        """Format content for Reddit with markdown support."""
        processed_lines = SocialMediaFormatter._preprocess_content(content)
        
        # Add Reddit-style markdown
        formatted_lines = ['# Ergo Platform Update']
        formatted_lines.extend([f"- {line}" for line in processed_lines])
        
        # Reddit footer
        formatted_lines.append(
            "\n---\n*Updates sourced from Ergo Discord. "
            "Join our [Discord Community](https://discord.gg/ergo-platform)*"
        )
        
        return '\n'.join(formatted_lines)
