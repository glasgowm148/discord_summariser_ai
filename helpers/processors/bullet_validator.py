"""Validates updates and their components."""
import re
from typing import List, Tuple, Union, Optional

from models.bullet_point import BulletPoint
from services.base_service import BaseService
from helpers.processors.text_processor import TextProcessor


class BulletValidator(BaseService):
    """Handles validation of updates and their components."""

    def __init__(self, server_id: str):
        super().__init__()
        self.server_id = server_id

    def initialize(self) -> None:
        """No initialization needed for validator."""
        pass

    def validate_bullet(self, bullet: Union[BulletPoint, str]) -> Tuple[bool, List[str]]:
        """Validate an update and return validation status and messages."""
        validation_messages = []

        # Handle different input types
        if isinstance(bullet, str):
            # Convert string to a basic BulletPoint if needed
            bullet = BulletPoint(
                content=bullet,
                discord_link=TextProcessor.extract_discord_url(bullet),
                project_name=self._extract_project_name(bullet)
            )

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

    def _extract_project_name(self, content: str) -> Optional[str]:
        """Extract project name from content."""
        # Try to extract from bold text
        match = re.search(r'\*\*([^*]+)\*\*', content)
        if match:
            return match.group(1).strip()
        
        # Fallback: use first significant word
        words = re.findall(r'\b\w+\b', content)
        for word in words:
            if len(word) > 2 and word.lower() not in {'the', 'and', 'but', 'for', 'with', 'has', 'was', 'are'}:
                return word
        
        return None

    def validate_bullet_verbose(self, bullet: Union[BulletPoint, str]) -> str:
        """Return detailed validation results for logging."""
        # Handle different input types
        if isinstance(bullet, str):
            # Convert string to a basic BulletPoint if needed
            bullet = BulletPoint(
                content=bullet,
                discord_link=TextProcessor.extract_discord_url(bullet),
                project_name=self._extract_project_name(bullet)
            )

        result = []

        # Format validation
        if re.match(r'^[\U0001F300-\U0001F9FF]', bullet.content.strip()):
            result.append("✓ Format")
        else:
            result.append("❌ Format")

        # Link validation
        if bullet.discord_link:
            if self._validate_discord_link(bullet.discord_link):
                result.append("✓ Link")
            else:
                result.append("❌ Invalid Link Format")
        else:
            result.append("❌ Link")

        # Length validation
        length = len(bullet.content.strip())
        if length > 50:
            result.append(f"✓ Length ({length})")
        else:
            result.append(f"❌ Length ({length})")

        # Project validation
        if bullet.project_name:
            result.append(f"✓ Project: {bullet.project_name}")
        else:
            result.append("⚠️ No project")

        return " | ".join(result)

    def validate_bullets(self, bullets: List[Union[BulletPoint, str]]) -> List[str]:
        """
        Validate multiple bullets and return verbose validation results.
        
        Allows input of either BulletPoint objects or strings.
        """
        return [self.validate_bullet_verbose(bullet) for bullet in bullets]
