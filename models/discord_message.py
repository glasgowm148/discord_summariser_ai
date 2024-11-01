from dataclasses import dataclass

@dataclass
class DiscordMessage:
    channel_id: str
    channel_category: str
    channel_name: str
    message_id: str
    message_content: str
    author_name: str
    timestamp: str
