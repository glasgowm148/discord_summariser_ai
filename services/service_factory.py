"""Factory for creating service instances."""

import os
from typing import Optional

from openai import OpenAI

from services.bullet_processor import BulletProcessor
from services.bullet_validator import BulletValidator
from services.chunk_processor import ChunkProcessor
from services.csv_loader import CsvLoaderService
from services.discord_link_processor import DiscordLinkProcessor
from services.discord_service import DiscordService
from services.meta_service import MetaService
from services.reddit_service import RedditService
from services.summary_finalizer import SummaryFinalizer
from services.summary_generator import SummaryGenerator
from services.text_processor import TextProcessor

class ServiceFactory:
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'ServiceFactory':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def create_bullet_processor(self, api_key: str, server_id: str) -> BulletProcessor:
        """Create a BulletProcessor instance with all required dependencies."""
        # Create OpenAI client
        openai_client = OpenAI(api_key=api_key)
        
        # Create required service instances
        text_processor = TextProcessor()
        bullet_validator = BulletValidator(server_id=server_id)
        discord_link_processor = DiscordLinkProcessor(server_id=server_id)
        
        # Create and return BulletProcessor with dependencies
        return BulletProcessor(
            text_processor=text_processor,
            bullet_validator=bullet_validator,
            discord_link_processor=discord_link_processor,
            openai_client=openai_client
        )
        
    def create_chunk_processor(self) -> ChunkProcessor:
        """Create a ChunkProcessor instance."""
        return ChunkProcessor()
        
    def create_csv_loader(self) -> CsvLoaderService:
        """Create a CsvLoaderService instance."""
        return CsvLoaderService()
        
    def create_discord_service(self) -> Optional[DiscordService]:
        """Create a DiscordService instance."""
        return DiscordService()
        
    def create_meta_service(self) -> Optional[MetaService]:
        """Create a MetaService instance."""
        return MetaService()
        
    def create_reddit_service(self) -> Optional[RedditService]:
        """Create a RedditService instance."""
        return RedditService()
        
    def create_summary_finalizer(self, api_key: str) -> SummaryFinalizer:
        """Create a SummaryFinalizer instance."""
        return SummaryFinalizer(api_key)
        
    def create_summary_generator(self, api_key: str) -> SummaryGenerator:
        """Create a SummaryGenerator instance."""
        return SummaryGenerator(api_key)
        
    def create_text_processor(self) -> TextProcessor:
        """Create a TextProcessor instance."""
        return TextProcessor()
