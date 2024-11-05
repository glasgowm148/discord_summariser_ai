"""Handles processing and fixing of Discord links."""
import re
from typing import Optional

from services.base_service import BaseService


class DiscordLinkProcessor(BaseService):
    """Handles processing and fixing of Discord links."""

    def __init__(self, server_id: str):
        super().__init__()
        self.server_id = server_id

    def initialize(self) -> None:
        """No initialization needed for link processor."""
        pass

    def extract_link_components(self, link: str) -> Optional[tuple[str, str, str]]:
        """Extract server_id, channel_id, and message_id from a Discord link."""
        match = re.search(r'https://discord\.com/channels/(\d+)/(\d+)/(\d+)', link)
        if match:
            return match.group(1), match.group(2), match.group(3)
        return None

    def fix_discord_link(self, content: str, chunk: str) -> Optional[str]:
        """Try to fix a Discord link using message metadata from the chunk."""
        try:
            message_match = re.search(r"Message ID: (\d+)", chunk)
            channel_match = re.search(r"Channel ID: (\d+) ", chunk)

            if message_match and channel_match:
                message_id = message_match.group(1)
                channel_id = channel_match.group(1)
                correct_link = f"https://discord.com/channels/{self.server_id}/{channel_id}/{message_id}"

                # Replace the incorrect link with the correct one
                fixed_content = re.sub(
                    r"\(https://discord\.com/channels/[^)]+\)",
                    f"({correct_link})",
                    content,
                )

                return fixed_content

        except Exception as e:
            self.logger.warning(f"Error fixing Discord link: {e}")
            return None

    def build_discord_link(self, channel_id: str, message_id: str) -> str:
        """Build a Discord link from components."""
        return f"https://discord.com/channels/{self.server_id}/{channel_id}/{message_id}"

    def extract_message_metadata(self, chunk: str) -> tuple[Optional[str], Optional[str]]:
        """Extract message and channel IDs from a chunk of text."""
        message_id = None
        channel_id = None

        message_match = re.search(r"Message ID: (\d+)", chunk)
        if message_match:
            message_id = message_match.group(1)

        channel_match = re.search(r"Channel ID: (\d+)", chunk)
        if channel_match:
            channel_id = channel_match.group(1)

        return message_id, channel_id
