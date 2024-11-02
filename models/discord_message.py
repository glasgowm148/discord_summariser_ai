from dataclasses import dataclass

@dataclass
class DiscordMessage:
    server_id: str
    channel_id: str
    channel_category: str
    channel_name: str
    message_id: str
    message_content: str
    author_name: str
    timestamp: str

    @property
    def discord_link(self) -> str:
        """Generate the Discord link from server_id, channel_id, and message_id."""
        return f"https://discord.com/channels/{self.server_id}/{self.channel_id}/{self.message_id}"
