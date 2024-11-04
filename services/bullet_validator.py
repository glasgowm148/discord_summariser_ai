"""Validates updates and their components."""
import re
from typing import List, Tuple

from models.bullet_point import BulletPoint
from services.base_service import BaseService


class BulletValidator(BaseService):
    """Handles validation of updates and their components."""

    def __init__(self, server_id: str):
        super().__init__()
        self.server_id = server_id

    def initialize(self) -> None:
        """No initialization needed for validator."""
        pass

    def validate_bullet(self, bullet: BulletPoint) -> Tuple[bool, List[str]]:
        """Validate an update and return validation status and messages."""
        validation_messages = []

        # Check basic format - should start with an emoji
        if not re.match(r'^[\U0001F300-\U0001F9FF]', bullet.content.strip()):
            validation_messages.append("Does not start with emoji")
            return False, validation_messages

        # Check content length
        if len(bullet.content.strip()) <= 50:
            validation_messages.append("Too short")
            return False, validation_messages

        # Validate Discord link if present
        if bullet.discord_link:
            if not self._validate_discord_link(bullet.discord_link):
                validation_messages.append("Invalid Discord link format")
                return False, validation_messages
        else:
            validation_messages.append("Missing Discord link")
            return False, validation_messages

        return True, validation_messages

    def _validate_discord_link(self, link: str) -> bool:
        """Validate Discord link format."""
        pattern = f"^https://discord\\.com/channels/{self.server_id}/\\d+/\\d+$"
        return bool(re.match(pattern, link))

    def validate_bullet_verbose(self, bullet: BulletPoint) -> str:
        """Return detailed validation results for logging."""
        result = []

        if re.match(r'^[\U0001F300-\U0001F9FF]', bullet.content.strip()):
            result.append("✓ Format")
        else:
            result.append("❌ Format")

        if bullet.discord_link:
            if self._validate_discord_link(bullet.discord_link):
                result.append("✓ Link")
            else:
                result.append("❌ Invalid Link Format")
        else:
            result.append("❌ Link")

        length = len(bullet.content.strip())
        if length > 50:
            result.append(f"✓ Length ({length})")
        else:
            result.append(f"❌ Length ({length})")

        if bullet.project_name:
            result.append(f"✓ Project: {bullet.project_name}")
        else:
            result.append("⚠️ No project")

        if bullet.channel_name:
            result.append(f"✓ Channel: {bullet.channel_name}")

        return " | ".join(result)
