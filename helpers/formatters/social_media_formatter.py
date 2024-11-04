"""Platform-specific formatting for social media."""

from helpers.formatters.content_formatter import ContentFormatter


class SocialMediaFormatter:
    @staticmethod
    def format_for_platform(content: str, platform: str) -> str:
        """Format content for a specific social media platform."""
        formatters = {
            'twitter': SocialMediaFormatter.format_for_twitter,
            'facebook': SocialMediaFormatter.format_for_facebook,
            'instagram': SocialMediaFormatter.format_for_instagram
        }
        
        formatter = formatters.get(platform.lower())
        if not formatter:
            raise ValueError(f"Unsupported platform: {platform}")
            
        return formatter(content)

    @staticmethod
    def format_for_twitter(content: str) -> str:
        """Format content for Twitter."""
        formatted_lines = []
        
        for line in content.split('\n'):
            if not line.strip():
                continue

            # Remove section headers formatting
            if line.startswith('#'):
                line = line.lstrip('#').strip()
                formatted_lines.append(line)
                continue

            # Remove formatting but keep content
            line = ContentFormatter.format_bullet_point(line)
            formatted_lines.append(line)

        formatted_content = '\n'.join(formatted_lines).strip()

        # Ensure content fits Twitter's character limit
        if len(formatted_content) > 280:
            # Truncate and add ellipsis
            formatted_content = formatted_content[:277] + "..."

        return formatted_content

    @staticmethod
    def format_for_facebook(content: str) -> str:
        """Format content for Facebook."""
        formatted_lines = []
        
        for line in content.split('\n'):
            if not line.strip():
                continue

            # Convert section headers to Facebook-style formatting
            if line.startswith('#'):
                line = line.lstrip('#').strip().upper()
                formatted_lines.extend(['', '📢 ' + line, ''])
                continue

            # Format bullet points
            line = ContentFormatter.format_bullet_point(line)
            formatted_lines.append(line)

        formatted_content = '\n'.join(formatted_lines).strip()

        # Add Facebook-specific call to action
        return formatted_content + (
            "\n\n🔗 Join our Discord community for real-time updates and discussions: "
            "https://discord.gg/ergo-platform-668903786361651200"
        )

    @staticmethod
    def format_for_instagram(content: str) -> str:
        """Format content for Instagram."""
        formatted_lines = []
        
        for line in content.split('\n'):
            if not line.strip():
                continue

            # Convert section headers to Instagram-style formatting
            if line.startswith('#'):
                line = line.lstrip('#').strip().upper()
                formatted_lines.extend(['', '🚀 ' + line + ' 🚀', ''])
                continue

            # Format bullet points
            line = ContentFormatter.format_bullet_point(line)
            formatted_lines.append(line)

        formatted_content = '\n'.join(formatted_lines).strip()

        # Add Instagram-specific hashtags and call to action
        hashtags = (
            "\n\n.\n.\n.\n"
            "#Ergo #Blockchain #Cryptocurrency #CryptoNews #BlockchainDevelopment "
            "#DeFi #CryptoTechnology #Ergonauts #CryptoInnovation #BlockchainInnovation "
            "#CryptoUpdates #BlockchainUpdates"
        )
        
        return formatted_content + hashtags + "\n\n💫 Join our Discord community for real-time updates! Link in bio."
