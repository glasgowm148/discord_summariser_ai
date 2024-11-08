"""Base class for update processing."""
from typing import List, Optional
from services.base_service import BaseService
from models.bullet_point import BulletPoint


class BaseUpdateProcessor(BaseService):
    """Base class for processing updates with common functionality."""

    def __init__(self):
        """Initialize the base update processor."""
        super().__init__()
        self.total_updates = 0
        self._last_processed_bullets: List[BulletPoint] = []

    def get_last_processed_bullets(self) -> List[BulletPoint]:
        """Retrieve the last processed bullets."""
        return self._last_processed_bullets

    def _create_update_point(self, text: str) -> BulletPoint:
        """
        Create a basic update point object from text.
        
        This method should be overridden by subclasses with more specific logic.
        """
        return BulletPoint(content=text)
