"""Update extraction utilities."""
import re
import logging
from typing import List, Dict

from openai import OpenAI
from utils.prompts import SummaryPrompts


class UpdateExtractor:
    """Handles extraction of updates from text chunks."""

    def __init__(self, openai_client: OpenAI, logger=None):
        """Initialize with OpenAI client."""
        self.client = openai_client
        self.logger = logger or logging.getLogger(__name__)

    def _extract_channel_context(self, chunk: str) -> Dict[str, List[str]]:
        """
        Extract context for each channel in the chunk, processing the entire chunk.
        
        :param chunk: Full text chunk
        :return: Dictionary of channel names to their message contents
        """
        self.logger.info(f"Processing chunk of length: {len(chunk)}")
        
        # Split chunk into message blocks preserving all content
        message_blocks = chunk.split('---\n')
        self.logger.info(f"Found {len(message_blocks)} message blocks")
        
        channel_context = {}
        
        for block in message_blocks:
            if not block.strip():
                continue
                
            # Extract exact channel name and message
            channel_match = re.search(r'Channel Name: ([^\n]+)', block)
            message_match = re.search(r'Message: (.+?)(?=Channel ID:|$)', block, re.DOTALL)
            
            if channel_match and message_match:
                channel_name = channel_match.group(1).strip()
                message = message_match.group(1).strip()
                
                if channel_name not in channel_context:
                    channel_context[channel_name] = []
                channel_context[channel_name].append(message)
        
        # Detailed logging of extracted channels
        self.logger.info("Extracted channels and message counts:")
        for channel, messages in channel_context.items():
            self.logger.info(f"- {channel}: {len(messages)} messages")
        
        return channel_context

    def extract_updates_from_chunk(
        self, 
        chunk: str, 
        retry_count: int = 0, 
        current_updates: int = 0
    ) -> List[str]:
        """Extract updates from chunk using OpenAI API."""
        channel_context = self._extract_channel_context(chunk)
        
        if not channel_context:
            self.logger.warning("No channels extracted from chunk")
            return []

        # Create detailed channel summaries for the prompt
        channel_summaries = []
        for channel, messages in channel_context.items():
            # Take a sample of messages to identify topics
            message_sample = messages[:3]
            channel_summary = (
                f"Channel '{channel}': {len(messages)} messages. "
                f"Sample: {' | '.join(message_sample)[:200]}..."
            )
            channel_summaries.append(channel_summary)

        # Construct a prompt that encourages coverage of all channels
        prompt = (
            SummaryPrompts.get_user_prompt(chunk, current_updates) +
            "\n\nCHANNEL STATISTICS AND CONTEXT:\n" + 
            "\n".join(channel_summaries) +
            "\n\nGUIDELINES:" +
            "\n1. Generate updates from ALL channels listed above" +
            "\n2. Maintain a balance of updates proportional to message counts" +
            "\n3. If no significant updates are found, generate at least 1-2 general observations"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SummaryPrompts.get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=min(0.7 + (retry_count * 0.05), 0.95),
                max_tokens=5000,
            )

            summary = response.choices[0].message.content
            
            # Process the updates
            updates = []
            for line in summary.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Ensure proper emoji prefix
                if not re.match(r'^[\U0001F300-\U0001F9FF]', line):
                    line = f"🔹 {line}"
                    
                # Verify the update references a valid channel or is a general observation
                channel_in_update = False
                for channel in channel_context.keys():
                    if f"**{channel}**" in line:
                        channel_in_update = True
                        break
                
                # Allow general observations if no channel-specific updates
                if channel_in_update or len(updates) < 2:
                    updates.append(line)
                    
            # If no updates found, generate a fallback update
            if not updates:
                self.logger.warning("No updates generated. Creating a fallback update.")
                updates.append("🔹 **General**: Ongoing discussions and community engagement observed.")
            
            return updates

        except Exception as e:
            self.logger.error(f"Error extracting updates: {e}")
            # Return a fallback update on error
            return ["🔹 **General**: Ongoing discussions and community engagement observed."]
