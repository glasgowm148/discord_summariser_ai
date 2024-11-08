# services/chunk_processor.py
from typing import List
from models.discord_message import DiscordMessage
import logging
import re
class ChunkProcessor:
    def __init__(self, max_chunk_size: int = 128000):
        self.MAX_CHUNK_SIZE = max_chunk_size
        self.logger = logging.getLogger(__name__)

    def split_messages_into_chunks(self, messages: List[DiscordMessage]) -> List[str]:
        """
        Split messages into chunks with more flexible and comprehensive approach.
        
        Key changes:
        1. Use full max chunk size
        2. Minimize filtering of messages
        3. Create larger, more comprehensive chunks
        4. Preserve message diversity
        """
        self.logger.info(f"Starting chunk processing for {len(messages)} messages")
        self.logger.info(f"Max chunk size: {self.MAX_CHUNK_SIZE} characters")
        
        # Sort messages by timestamp in reverse order (newest first)
        sorted_messages = sorted(messages, key=lambda x: x.timestamp, reverse=True)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for msg in sorted_messages:
            # Format message with comprehensive metadata
            formatted_msg = (
                f"Channel Name: {msg.channel_name}\n"
                f"Channel Category: {msg.channel_category}\n"
                f"Author: {msg.author_name}\n"
                f"Message: {msg.message_content}\n"
                f"Channel ID: {msg.channel_id}\n"
                f"Message ID: {msg.message_id}\n"
                f"Timestamp: {msg.timestamp}\n"
                "---\n"
            )
            
            msg_size = len(formatted_msg)
            
            # More flexible chunk creation
            if current_size + msg_size > self.MAX_CHUNK_SIZE:
                # When chunk is full, create a new chunk
                if current_chunk:
                    chunk_content = '\n'.join(current_chunk)
                    chunks.append(chunk_content)
                    self.logger.info(f"Chunk created with size {len(chunk_content)} characters")
                
                # Reset for new chunk
                current_chunk = [formatted_msg]
                current_size = msg_size
            else:
                # Add message to current chunk
                current_chunk.append(formatted_msg)
                current_size += msg_size
        
        # Add final chunk if not empty
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append(chunk_content)
            self.logger.info(f"Final chunk created with size {len(chunk_content)} characters")
        
        self.logger.info(f"Total chunks created: {len(chunks)}")
        
        # Log chunk details for verification
        for i, chunk in enumerate(chunks, 1):
            # Count unique channels in chunk
            channel_names = set(re.findall(r'Channel Name: (\w+)', chunk))
            message_count = len(re.findall(r'---\n', chunk))
            self.logger.info(f"Chunk {i}: {message_count} messages, Channels: {', '.join(channel_names)}")
        
        return chunks
