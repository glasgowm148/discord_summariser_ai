"""Optimize and process text chunks for efficient processing."""
import re
from typing import List, Optional

class ChunkOptimizer:
    """Handles optimization and processing of text chunks."""
    
    @staticmethod
    def optimize_chunk_size(chunk: str, target_length: int = 100000) -> str:
        """Optimize chunk size while preserving context and structure."""
        # Extract channel name if present
        channel_name = ChunkOptimizer._extract_channel_name(chunk)
        
        # Split chunk into messages if it contains message separators
        messages = chunk.split("---\n")

        # If it's a single message or doesn't use separators, return as is
        if len(messages) <= 1:
            return chunk

        # Process messages in reverse chronological order (most recent first)
        optimized_messages = []
        current_length = 0

        for msg in messages:
            msg_length = len(msg) + 4  # Add 4 for the separator
            if current_length + msg_length > target_length:
                break
                
            # Add channel context if available and needed
            processed_msg = ChunkOptimizer._add_channel_context(msg, channel_name)
            optimized_messages.append(processed_msg)
            current_length += msg_length

        # Return optimized chunk
        if optimized_messages:
            return "---\n".join(optimized_messages) + "---\n"
        return messages[0] + "---\n"  # Fallback to first message if optimization fails

    @staticmethod
    def split_into_processable_chunks(text: str, max_chunk_size: int = 100000) -> List[str]:
        """Split text into processable chunks while preserving message boundaries."""
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        current_chunk = []
        current_size = 0
        
        messages = text.split("---\n")
        
        for message in messages:
            message_size = len(message) + 4  # Add 4 for the separator
            
            if current_size + message_size > max_chunk_size and current_chunk:
                # Finalize current chunk
                chunks.append("---\n".join(current_chunk) + "---\n")
                current_chunk = []
                current_size = 0
            
            current_chunk.append(message)
            current_size += message_size
        
        # Add remaining messages
        if current_chunk:
            chunks.append("---\n".join(current_chunk) + "---\n")
        
        return chunks

    @staticmethod
    def _extract_channel_name(chunk: str) -> Optional[str]:
        """Extract channel name from chunk if present."""
        channel_match = re.search(r'Channel:\s*([^\n]+)', chunk)
        return channel_match.group(1) if channel_match else None

    @staticmethod
    def _add_channel_context(message: str, channel_name: Optional[str]) -> str:
        """Add channel context to message if needed."""
        if not channel_name or "Channel:" in message:
            return message
        return f"Channel: {channel_name}\n{message}"

    @staticmethod
    def merge_similar_chunks(chunks: List[str], similarity_threshold: float = 0.3) -> List[str]:
        """Merge similar chunks to reduce redundancy while preserving context."""
        if len(chunks) <= 1:
            return chunks

        merged_chunks = []
        skip_indices = set()

        for i, chunk1 in enumerate(chunks):
            if i in skip_indices:
                continue

            similar_chunks = []
            for j, chunk2 in enumerate(chunks[i + 1:], start=i + 1):
                if j not in skip_indices and ChunkOptimizer._are_chunks_similar(chunk1, chunk2, similarity_threshold):
                    similar_chunks.append(chunk2)
                    skip_indices.add(j)

            if similar_chunks:
                # Merge similar chunks while preserving unique content
                merged_chunk = ChunkOptimizer._merge_chunks([chunk1] + similar_chunks)
                merged_chunks.append(merged_chunk)
                skip_indices.add(i)
            elif i not in skip_indices:
                merged_chunks.append(chunk1)

        return merged_chunks

    @staticmethod
    def _are_chunks_similar(chunk1: str, chunk2: str, threshold: float) -> bool:
        """Determine if two chunks are similar based on content overlap."""
        words1 = set(re.findall(r'\b\w+\b', chunk1.lower()))
        words2 = set(re.findall(r'\b\w+\b', chunk2.lower()))
        
        if not words1 or not words2:
            return False

        intersection = words1.intersection(words2)
        smaller_set = min(len(words1), len(words2))
        
        return len(intersection) / smaller_set >= threshold

    @staticmethod
    def _merge_chunks(chunks: List[str]) -> str:
        """Merge multiple chunks while preserving unique content and structure."""
        # Split chunks into messages
        all_messages = []
        seen_messages = set()
        
        for chunk in chunks:
            messages = chunk.split("---\n")
            for msg in messages:
                # Create a normalized version for comparison
                normalized = re.sub(r'\s+', ' ', msg.lower().strip())
                if normalized and normalized not in seen_messages:
                    all_messages.append(msg)
                    seen_messages.add(normalized)
        
        return "---\n".join(all_messages) + "---\n" if all_messages else ""
