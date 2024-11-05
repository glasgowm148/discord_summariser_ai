# services/chunk_processor.py
from typing import List
from models.discord_message import DiscordMessage

class ChunkProcessor:
    def __init__(self, max_chunk_size: int = 128000):
        self.MAX_CHUNK_SIZE = max_chunk_size

    def split_messages_into_chunks(self, messages: List[DiscordMessage]) -> List[str]:
        chunks = []
        current_chunk = []
        current_size = 0
        
        # Sort messages by timestamp in reverse order (newest first)
        sorted_messages = sorted(messages, key=lambda x: x.timestamp, reverse=True)
        
        for msg in sorted_messages:
            formatted_msg = (
                f"Channel: {msg.channel_name}\n"  # Only use channel_name, not the category
                f"Author: {msg.author_name}\n"
                f"Message: {msg.message_content}\n"
                f"Channel ID: {msg.channel_id}\n"  # Make channel_id more prominent
                f"Message ID: {msg.message_id}\n"  # Make message_id more prominent
                f"Timestamp: {msg.timestamp}\n"
                "---\n"
            )
            
            msg_size = len(formatted_msg)
            
            if current_size + msg_size > self.MAX_CHUNK_SIZE:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [formatted_msg]
                current_size = msg_size
            else:
                current_chunk.append(formatted_msg)
                current_size += msg_size
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
