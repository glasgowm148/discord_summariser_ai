"""Factory for creating service instances with dependency injection."""
import os
from typing import Optional

from openai import OpenAI

from services.base_service import BaseService
from services.bullet_processor import BulletProcessor
from services.bullet_validator import BulletValidator
from services.chunk_processor import ChunkProcessor
from services.discord_link_processor import DiscordLinkProcessor
from services.hackmd_service import HackMDService
from services.summary_finalizer import SummaryFinalizer
from services.summary_generator import SummaryGenerator
from services.text_processor import TextProcessor
from services.discord_service import DiscordService


class ServiceFactory:
    """Centralized factory for creating service instances."""

    _instance = None

    def __init__(self):
        """Initialize factory with default dependencies."""
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    @classmethod
    def get_instance(cls):
        """Singleton pattern to get or create factory instance."""
        if not cls._instance:
            cls._instance = ServiceFactory()
        return cls._instance

    def create_text_processor(self) -> TextProcessor:
        """Create a TextProcessor instance."""
        return TextProcessor()

    def create_bullet_validator(
        self, 
        server_id: Optional[str] = None
    ) -> BulletValidator:
        """Create a BulletValidator instance."""
        return BulletValidator(
            server_id=server_id or os.getenv('DISCORD_SERVER_ID', '')
        )

    def create_discord_link_processor(
        self, 
        server_id: Optional[str] = None
    ) -> DiscordLinkProcessor:
        """Create a DiscordLinkProcessor instance."""
        return DiscordLinkProcessor(
            server_id=server_id or os.getenv('DISCORD_SERVER_ID', '')
        )

    def create_chunk_processor(self) -> ChunkProcessor:
        """Create a ChunkProcessor instance."""
        return ChunkProcessor()

    def create_bullet_processor(
        self, 
        api_key: Optional[str] = None, 
        server_id: Optional[str] = None
    ) -> BulletProcessor:
        """Create a BulletProcessor instance with dependencies."""
        return BulletProcessor(
            text_processor=self.create_text_processor(),
            bullet_validator=self.create_bullet_validator(server_id),
            discord_link_processor=self.create_discord_link_processor(server_id),
            openai_client=self.openai_client
        )

    def create_summary_finalizer(
        self, 
        api_key: Optional[str] = None
    ) -> SummaryFinalizer:
        """Create a SummaryFinalizer instance."""
        return SummaryFinalizer(
            api_key=api_key or os.getenv('OPENAI_API_KEY', '')
        )

    def create_hackmd_service(
        self, 
        api_key: Optional[str] = None
    ) -> HackMDService:
        """Create a HackMDService instance."""
        return HackMDService(
            api_key=api_key or os.getenv('HACKMD_API_KEY')
        )

    def create_discord_service(self) -> DiscordService:
        """Create a DiscordService instance."""
        return DiscordService()

    def create_summary_generator(
        self, 
        api_key: Optional[str] = None
    ) -> SummaryGenerator:
        """Create a SummaryGenerator instance with dependencies."""
        server_id = os.getenv('DISCORD_SERVER_ID', '')
        return SummaryGenerator(
            api_key=api_key or os.getenv('OPENAI_API_KEY', ''),
            chunk_processor=self.create_chunk_processor(),
            bullet_processor=self.create_bullet_processor(api_key, server_id),
            summary_finalizer=self.create_summary_finalizer(api_key),
            hackmd_service=self.create_hackmd_service(),
            discord_service=self.create_discord_service()
        )
