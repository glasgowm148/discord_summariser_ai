"""Core text processing service."""
from typing import List, Dict, Optional

from services.base_service import BaseService
from helpers.processors.text_cleaner import TextCleaner
from helpers.processors.content_relationship_analyzer import ContentRelationshipAnalyzer
from helpers.processors.chunk_optimizer import ChunkOptimizer

class TextProcessor(BaseService):
    """Handles core text processing operations."""

    def __init__(self):
        super().__init__()

    def initialize(self) -> None:
        """No initialization needed for text processor."""
        pass

    def simplify_project_name(self, project_name: str) -> str:
        """Simplify and standardize project names."""
        # Convert to lowercase and remove common suffixes
        simplified = TextCleaner.remove_common_suffixes(project_name)
        # Return original first word with original capitalization
        return project_name.split()[0]

    def find_related_bullets(self, bullets: List[str]) -> Dict[str, List[str]]:
        """Find groups of related bullets based on content similarity."""
        return ContentRelationshipAnalyzer.find_related_content(bullets)

    def combine_related_bullets(self, bullets: List[str]) -> str:
        """Combine related bullets into a single comprehensive bullet point."""
        return ContentRelationshipAnalyzer.combine_related_content(bullets)

    def clean_bot_references(self, bullet: str) -> str:
        """Clean up bot references in bullet points."""
        return TextCleaner.clean_bot_references(bullet)

    def optimize_chunk_size(self, chunk: str, target_length: int = 100000) -> str:
        """Optimize chunk size for processing."""
        return ChunkOptimizer.optimize_chunk_size(chunk, target_length)

    def split_chunks(self, text: str, max_chunk_size: int = 100000) -> List[str]:
        """Split text into processable chunks."""
        return ChunkOptimizer.split_into_processable_chunks(text, max_chunk_size)

    def merge_similar_chunks(self, chunks: List[str], similarity_threshold: float = 0.3) -> List[str]:
        """Merge similar chunks to reduce redundancy."""
        return ChunkOptimizer.merge_similar_chunks(chunks, similarity_threshold)

    def standardize_text(self, text: str) -> str:
        """Standardize text formatting and structure."""
        text = TextCleaner.clean_bot_references(text)
        text = TextCleaner.standardize_whitespace(text)
        return text

    def extract_content_without_formatting(self, text: str) -> str:
        """Extract plain content without markdown formatting."""
        return TextCleaner.extract_content_without_formatting(text)
