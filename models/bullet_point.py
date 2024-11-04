"""Represents a processed bullet point."""
from dataclasses import dataclass, field
from typing import List

@dataclass
class BulletPoint:
    """Represents a processed bullet point."""
    content: str
    project_name: str = ""
    discord_link: str = ""
    is_valid: bool = False
    validation_messages: List[str] = field(default_factory=list)
    channel_id: str = ""
    message_id: str = ""
    channel_name: str = ""  # Added to track channel context
