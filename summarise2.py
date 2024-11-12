#!/usr/bin/env python3
"""
Simplified Discord Summary Generator

Reads a CSV file of Discord messages and generates a concise summary.
"""

import os
import re
import json
import logging
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd
from openai import OpenAI
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from tabulate import tabulate
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.markdown import Markdown
import inquirer  # Add this import for interactive prompts

from utils.prompts import SummaryPrompts
from services.social_media.discord_service import DiscordService  # Import Discord service

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DiscordSummarizer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize summarizer with OpenAI client."""
        self.api_key = os.getenv('OPENAI_API_KEY', api_key)
        self.client = OpenAI(api_key=self.api_key)
        self.stats: Dict[str, int] = {}
        self.console = Console()
        self.channel_distribution: Dict[str, int] = {}
        self.current_date = datetime.now(ZoneInfo('UTC'))
        self.recent_topics_file = os.path.join('output', 'recent_topics.json')
        self.TOPIC_EXPIRY_DAYS = 7  # Topics expire after 7 days
        self.MAX_TOKENS = 100000  # Reduced from 128000 to leave room for system/user prompts

    def _normalize_topic(self, topic: str) -> str:
        """
        Normalize topic for consistent comparison.
        
        Args:
            topic: Raw topic string
        
        Returns:
            Normalized topic string
        """
        # Convert to lowercase, remove punctuation, strip whitespace
        return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', topic.lower())).strip()

    def _load_recent_topics(self) -> List[str]:
        """
        Load topics from recent summaries to avoid repetition.
        
        Returns:
            List of recent discussion topics
        """
        try:
            # If recent topics file exists, load it
            if os.path.exists(self.recent_topics_file):
                with open(self.recent_topics_file, 'r') as f:
                    recent_topics = json.load(f)
                
                # Filter out topics older than specified days
                cutoff_date = self.current_date - timedelta(days=self.TOPIC_EXPIRY_DAYS)
                
                # Filter and normalize topics
                filtered_topics = {
                    topic: timestamp for topic, timestamp in recent_topics.items()
                    if datetime.fromisoformat(timestamp) > cutoff_date
                }
                
                # Update the file with filtered topics
                with open(self.recent_topics_file, 'w') as f:
                    json.dump(filtered_topics, f, indent=2)
                
                return list(filtered_topics.keys())
            
            return []
        
        except Exception as e:
            logger.error(f"Error loading recent topics: {e}")
            return []

    def _update_recent_topics(self, new_topics: List[str]):
        """
        Update the recent topics file with new topics.
        
        Args:
            new_topics: List of new discussion topics to add
        """
        try:
            # Load existing topics
            recent_topics = {}
            if os.path.exists(self.recent_topics_file):
                with open(self.recent_topics_file, 'r') as f:
                    recent_topics = json.load(f)
            
            # Normalize and add new topics with current timestamp
            for topic in new_topics:
                normalized_topic = self._normalize_topic(topic)
                recent_topics[normalized_topic] = self.current_date.isoformat()
            
            # Write back to file
            with open(self.recent_topics_file, 'w') as f:
                json.dump(recent_topics, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error updating recent topics: {e}")

    def _extract_summary_topics(self, summary: str) -> List[str]:
        """
        Extract key topics from the generated summary.
        
        Args:
            summary: Generated summary text
        
        Returns:
            List of extracted topics
        """
        # Extract topics from bullet points
        topic_pattern = r'\*\*([^*]+)\*\*'
        topics = re.findall(topic_pattern, summary)
        
        # Clean, normalize, and filter topics
        cleaned_topics = [
            topic.strip() 
            for topic in topics 
            if len(topic.strip()) > 3  # Avoid very short topics
        ]
        
        return cleaned_topics

    def _chunk_messages(self, messages_with_links: List[Tuple[str, str, str]], max_tokens: int = 100000) -> List[List[Tuple[str, str, str]]]:
        """
        Enhanced message chunking with more intelligent token estimation and context preservation.
        
        Args:
            messages_with_links: List of message tuples
            max_tokens: Maximum tokens per chunk
        
        Returns:
            List of message chunks
        """
        def estimate_tokens(message: Tuple[str, str, str]) -> int:
            """More precise token estimation."""
            # Use a more conservative token estimation
            # Approximately 1 token ≈ 3.5 characters for technical text
            return len(f"{message[0]} {message[1]} {message[2]}") // 3.5

        def is_high_quality_message(message: Tuple[str, str, str]) -> bool:
            """
            Determine if a message is high-quality and worth including.
            
            Criteria:
            - Contains technical keywords
            - Longer than 50 characters
            - Not a generic or repetitive message
            """
            technical_keywords = [
                'development', 'protocol', 'implementation', 'architecture', 
                'design', 'algorithm', 'optimization', 'research', 'innovation'
            ]
            
            message_text = message[0].lower()
            
            return (
                len(message_text) > 50 and  # Substantial message length
                any(keyword in message_text for keyword in technical_keywords) and  # Contains technical content
                not re.search(r'\b(hi|hello|thanks|thank you|ok|okay)\b', message_text)  # Exclude generic messages
            )

        chunks = []
        current_chunk = []
        current_chunk_tokens = 0

        # Sort messages by potential relevance
        sorted_messages = sorted(
            messages_with_links, 
            key=lambda msg: is_high_quality_message(msg), 
            reverse=True
        )

        for message in sorted_messages:
            message_tokens = estimate_tokens(message)
            
            # If adding this message would exceed max tokens, start a new chunk
            if current_chunk_tokens + message_tokens > max_tokens:
                chunks.append(current_chunk)
                current_chunk = []
                current_chunk_tokens = 0
            
            # Only add high-quality messages
            if is_high_quality_message(message):
                current_chunk.append(message)
                current_chunk_tokens += message_tokens
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _deduplicate_chunks(self, chunks: List[List[Tuple[str, str, str]]]) -> List[Tuple[str, str, str]]:
        """
        Deduplicate messages across chunks.
        
        Args:
            chunks: List of message chunks
        
        Returns:
            Deduplicated list of messages
        """
        seen_messages = set()
        deduplicated_messages = []

        for chunk in chunks:
            for message in chunk:
                # Use message content for deduplication
                message_key = message[0].lower().strip()
                
                if message_key not in seen_messages:
                    seen_messages.add(message_key)
                    deduplicated_messages.append(message)
        
        return deduplicated_messages

    def _preprocess_messages(self, df: pd.DataFrame) -> List[Tuple[str, str, str]]:
        """
        Preprocess messages to extract meaningful content with links and channel names.
        
        Returns list of (message_content, discord_link, channel_name) tuples
        """
        self.console.print("[bold blue]🔍 Preprocessing Messages...[/bold blue]")
        
        # Ensure consistent timezone
        date_threshold = self.current_date - timedelta(days=5)
        
        try:
            # Convert timestamp to timezone-aware datetime with flexible parsing
            df['message_timestamp'] = pd.to_datetime(df['message_timestamp'], format='ISO8601', utc=True)
        except Exception as e:
            logger.error(f"Timestamp parsing error: {e}")
            logger.error(f"Problematic timestamps: {df['message_timestamp'].head()}")
            raise ValueError(f"Failed to parse timestamps: {e}")
        
        # Track total messages
        self.stats['total_messages'] = len(df)
        
        # Filter messages
        filtered_messages = df[
            (df['message_timestamp'] > date_threshold) &  # Recent messages
            (df['message_content'].str.len() > 30) &     # Meaningful length
            (~df['message_content'].str.lower().str.contains('bot')) &  # Exclude bot messages
            (~df['message_content'].str.lower().str.contains('automated')) &  # Exclude automated messages
            (~df['message_content'].str.lower().str.contains('price')) &  # Exclude price discussions
            (~df['message_content'].str.lower().str.contains('market')) &  # Exclude market discussions
            (~df['message_content'].str.lower().str.contains('value')) &  # Exclude value speculations
            (~df['message_content'].str.lower().str.contains('trading'))  # Exclude trading discussions
        ]
        
        # Track filtered messages and channel distribution
        self.stats['filtered_messages'] = len(filtered_messages)
        channel_counts = filtered_messages['channel_name'].value_counts()
        self.channel_distribution = dict(channel_counts)
        
        # Create list of (message, link, channel) tuples
        messages_with_links = []
        for _, row in filtered_messages.iterrows():
            # Construct Discord link
            discord_link = f"https://discord.com/channels/668903786361651200/{row['channel_id']}/{row['message_id']}"
            messages_with_links.append((
                row['message_content'], 
                discord_link, 
                row['channel_name']
            ))
        
        self.console.print(f"[green]✓ Processed {len(messages_with_links)} messages[/green]")
        return messages_with_links

    def generate_summary(self, messages_with_links: List[Tuple[str, str, str]]) -> str:
        """Generate a concise summary using OpenAI with chunking."""
        try:
            self.console.print("[bold blue]🤖 Generating Summary...[/bold blue]")
            
            # Load recent topics to exclude
            recent_topics = self._load_recent_topics()
            
            # Chunk messages to handle token limit
            message_chunks = self._chunk_messages(messages_with_links, self.MAX_TOKENS)
            
            # Deduplicate messages across chunks
            deduplicated_messages = self._deduplicate_chunks(message_chunks)
            
            # Prepare chunk for processing with explicit channel context
            chunk = "\n".join([
                f"Channel Name: {msg[2]}\nMessage: {msg[0]}\nLink: {msg[1]}"
                for msg in deduplicated_messages
            ])
            
            # Prepare prompt with EXTREMELY strict filtering and context preservation
            prompt = SummaryPrompts.get_user_prompt(chunk, 0) + (
                f"\n\nCRITICAL CONTEXT: Today's date is {self.current_date.strftime('%Y-%m-%d')}. "
                "CRITICAL DATE INTERPRETATION RULES:"
                "\n- ALL DATE REFERENCES MUST BE INTERPRETED IN PAST TENSE"
                "\n- For ANY event mentioned with a date BEFORE today, use PAST TENSE"
                "\n- EXPLICITLY REPHRASE future-sounding language to past tense"
                "\n- EXAMPLES OF CORRECTIONS:"
                "   * 'will be discussed' → 'was discussed'"
                "   * 'upcoming event on X date' → 'event that occurred on X date'"
                "   * 'will take place' → 'took place'"
                "\n\nEXTREMELY CRITICAL SUMMARY FORMATTING CRITERIA:"
                "\n- GENERATE BETWEEN 8-12 THEMATIC BULLET POINTS"
                "\n- COMPLETELY EXCLUDE ANY CONTENT RELATED TO:"
                "   * Price discussions"
                "   * Market sentiment"
                "   * Trading strategies"
                "   * Value speculations"
                "   * Cryptocurrency market analysis"
                f"\n- STRICTLY AVOID REPEATING TOPICS FROM RECENT DISCUSSIONS: {', '.join(recent_topics)}"
                "\n- GROUP updates by MEANINGFUL TOPICS, NOT channel names"
                "\n- TOPIC SELECTION RULES:"
                "   * Identify overarching themes across different channels"
                "   * Create DESCRIPTIVE, CONTEXT-RICH topic headers"
                "   * Avoid generic headers like 'Community Updates'"
                "   * Use specific, engaging topic names"
                "\n- LINK FORMATTING RULES (ABSOLUTELY MANDATORY):"
                "   * EVERY bullet point MUST contain a MEANINGFUL, KEYWORD-RICH hyperlink"
                "   * Links MUST be embedded WITHIN the text, NOT at the end"
                "   * Link text MUST capture the CORE ESSENCE of the update"
                "   * NEVER use generic link text like 'link' or '#'"
                "   * Use DESCRIPTIVE, ACTION-ORIENTED link text"
                "\n- TOPIC HEADER EXAMPLES:"
                "   * 'Protocol Development Insights'"
                "   * 'Cross-Chain Liquidity Innovations'"
                "   * 'Community Engagement Strategies'"
                "\n- LINK CREATION EXAMPLES:"
                "   * 🚀 **Cross-Chain Liquidity**: [Groundbreaking rsERG/ETH pool guide](https://discord.com/link) introduces comprehensive bridging process."
                "\n- ONLY include updates with GROUNDBREAKING technical innovations"
                "\n- ELIMINATE any updates that are:"
                "   * Trivial configuration discussions"
                "   * Personal experiences"
                "   * Minor troubleshooting"
                "   * Speculative conversations"
                "   * Negative or pessimistic updates"
                "   * Feedback"
                "   * Challenges"
                "\n- Prioritize updates that represent:"
                "   * Significant protocol improvements"
                "   * Strategic technological advancements"
                "   * Concrete development milestones"
                "   * Positive community progress"
                "   * Innovative project developments"
                "\n- ZERO redundancy"
                "\n- DO NOT INCLUDE A SUMMARY AT THE END."
                "\n- Include ONLY updates that would be considered NEWSWORTHY and IMPACTFUL"
                "\n- PRESERVE original message nuances"
                "\n- USE DIVERSE EMOJIS reflecting the update's CONTEXT"
                "\n\nSTRICTLY ADHERE to ALL formatting and topic integration guidelines!"
                "\n\nIF NO MEANINGFUL UPDATES EXIST AFTER FILTERING, RETURN 'No significant updates this week.'"
            )
            
            # Generate summary
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": SummaryPrompts.get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2000,  # Increased to allow more comprehensive summary
                temperature=0.2  # Slightly increased to allow more variation
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Track summary generation stats
            self.stats['summary_tokens'] = response.usage.total_tokens if response.usage else 0
            
            # Remove the extra "• -" if present and ensure clean bullet points
            summary = re.sub(r'^•\s*-\s*', '• ', summary, flags=re.MULTILINE)
            
            # Extract and update recent topics
            extracted_topics = self._extract_summary_topics(summary)
            self._update_recent_topics(extracted_topics)
            
            self.console.print("[green]✓ Summary Generated Successfully[/green]")
            return summary
        
        except Exception as e:
            self.console.print(f"[bold red]✗ Summary Generation Failed: {e}[/bold red]")
            return "Unable to generate summary due to an error."

    def save_summary(self, summary: str, output_file: str = None):
        """Save summary to markdown file."""
        try:
            self.console.print("[bold blue]💾 Saving Summary...[/bold blue]")
            
            # Default output directory 
            output_dir = os.path.join('output', 'daily_summaries')
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Create filename using current date
            date_str = self.current_date.strftime('%Y-%m-%d')
            output_file = os.path.join(output_dir, f'{date_str}_discord_summary.md')
            
            # Explicitly remove any text after the last bullet point
            summary_lines = summary.split('\n')
            
            # Find the index of the last bullet point
            bullet_lines = [line for line in summary_lines if line.startswith('•')]
            
            # If no bullet lines, use the entire summary
            if not bullet_lines:
                cleaned_summary_lines = summary_lines
            else:
                # Find the index of the last bullet point
                last_bullet_index = summary_lines.index(bullet_lines[-1])
                
                # Keep only lines up to and including the last bullet point
                cleaned_summary_lines = summary_lines[:last_bullet_index + 1]
            
            # Reconstruct summary
            cleaned_summary = '\n'.join(cleaned_summary_lines)
            
            # Prepare full markdown content with intro
            full_markdown = f"# Discord Summary for {date_str}\n\n{cleaned_summary}"
            
            # Save to file (will overwrite if exists)
            with open(output_file, 'w') as f:
                f.write(full_markdown)
            
            self.console.print(f"[green]✓ Summary Saved to {output_file}[/green]")
            return cleaned_summary
        
        except Exception as e:
            self.console.print(f"[bold red]✗ Failed to Save Summary: {e}[/bold red]")
            return summary

    def print_stats(self):
        """Print a detailed and visually appealing table of statistics."""
        # Create a Rich table for overall stats
        stats_table = Table(title="Summary Generation Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="magenta")
        
        stats_table.add_row("Total Messages", str(self.stats.get('total_messages', 0)))
        stats_table.add_row("Filtered Messages", str(self.stats.get('filtered_messages', 0)))
        stats_table.add_row("Summary Tokens Used", str(self.stats.get('summary_tokens', 0)))
        
        # Create a panel for channel distribution
        channel_list = Table(title="Channel Distribution")
        channel_list.add_column("Channel", style="cyan")
        channel_list.add_column("Message Count", style="magenta")
        
        for channel, count in sorted(self.channel_distribution.items(), key=lambda x: x[1], reverse=True):
            channel_list.add_row(channel, str(count))
        
        # Print tables
        self.console.print(stats_table)
        self.console.print(channel_list)

def main():
    # Path to input CSV
    input_csv = 'output/export-668903786361651200-04Nov_11Nov_233050_7d/json_cleaned_8d.csv'
    
    try:
        # Initialize summarizer
        summarizer = DiscordSummarizer()
        
        # Read CSV with progress
        summarizer.console.print("[bold blue]📂 Loading Messages...[/bold blue]")
        df = pd.read_csv(input_csv)
        summarizer.console.print("[green]✓ Messages Loaded Successfully[/green]")
        
        # Preprocess messages first to populate channel distribution
        messages_with_links = summarizer._preprocess_messages(df)
        
        # Print stats 
        summarizer.print_stats()
        
        # Generate summary
        summary = summarizer.generate_summary(messages_with_links)
        
        # Save summary
        saved_summary = summarizer.save_summary(summary)
        
        # Print summary at the end
        summarizer.console.print("\n[bold green]📋 Summary from Recent Discussions:[/bold green]")
        for line in saved_summary.split('\n'):
            if line.strip():
                summarizer.console.print(f"[cyan]•[/cyan] {line.strip()}")
        
        # Prompt to send to Discord
        questions = [
            inquirer.Confirm('send_to_discord', 
                             message="Would you like to send this summary to Discord?", 
                             default=False)
        ]
        answers = inquirer.prompt(questions)
        
        if answers and answers['send_to_discord']:
            # Initialize Discord service
            discord_service = DiscordService()
            
            # Prepare summary for Discord by removing extra newlines
            discord_summary_lines = [line.strip() for line in saved_summary.split('\n') if line.strip()]
            discord_summary = '\n'.join(discord_summary_lines)
            
            # Prepend the specified text to the summary
            summary_with_header = "## Summary of discussions from the past few days:\n\n" + discord_summary
            
            # Send daily message to Discord
            discord_service.send_daily_message(summary_with_header)
            summarizer.console.print("\n[bold green]📤 Summary sent to Discord successfully![/bold green]")
        
        summarizer.console.print("\n[bold green]🎉 Summary Generation Complete![/bold green]")
    
    except Exception as e:
        logger.error(f"Summary process failed: {e}")
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
