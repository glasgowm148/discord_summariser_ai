"""Script to build project knowledge base from historical Discord data."""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
from typing import List
import pandas as pd
from dotenv import load_dotenv
import pytz

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.csv_loader import CsvLoaderService
from services.summary_generator import SummaryGenerator
from services.project_manager import ProjectManager
from config.settings import OUTPUT_DIR, CONFIG_DIR
from utils.logging_config import setup_logging
import logging

def process_exports(days_per_summary: int = 7) -> None:
    """Process exported files to build knowledge base."""
    try:
        # Load environment variables
        env_path = CONFIG_DIR / '.env'
        if not env_path.exists():
            raise FileNotFoundError(
                "config/.env file not found. Please copy config/.env.example "
                "to config/.env and fill in your values."
            )
        load_dotenv(env_path)

        # Initialize services
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.error("OPENAI_API_KEY environment variable not set")
            sys.exit(1)

        csv_loader = CsvLoaderService()
        summary_generator = SummaryGenerator(api_key)
        project_manager = ProjectManager()

        # Get all CSV files in historical directory
        historical_dir = Path(OUTPUT_DIR) / 'historical'
        export_files = list(historical_dir.glob('*.csv'))

        if not export_files:
            logging.error("No export files found in output/historical/")
            return

        # Process each time period
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=365)
        current_date = start_date

        # Load all CSV files first
        all_messages = []
        for export_file in export_files:
            try:
                # Read CSV with specific options to handle linebreaks
                df = pd.read_csv(
                    export_file,
                    quoting=1,  # Quote all fields
                    escapechar='\\',  # Use backslash as escape character
                    doublequote=False,  # Don't use double quotes
                    encoding='utf-8'
                )
                
                # Create required columns
                df['Content'] = df['message_content']
                df['Author'] = df['author_name']
                df['Channel'] = df['channel_name']
                df['MessageId'] = df['message_id']
                df['Timestamp'] = pd.to_datetime(df['message_timestamp'])
                
                # Add to messages list
                all_messages.append(df)
                logging.info(f"Loaded {len(df)} messages from {export_file}")
            except Exception as e:
                logging.error(f"Error loading {export_file}: {e}")
                continue

        if not all_messages:
            logging.error("No valid messages found in exports")
            return

        # Combine all messages
        messages_df = pd.concat(all_messages, ignore_index=True)
        messages_df = messages_df.sort_values('Timestamp')
        logging.info(f"Total messages loaded: {len(messages_df)}")

        # Process each time period
        while current_date < end_date:
            period_end = min(current_date + timedelta(days=days_per_summary), end_date)
            logging.info(f"\nProcessing period: {current_date.date()} to {period_end.date()}")

            # Filter messages for this period
            period_df = messages_df[
                (messages_df['Timestamp'] >= current_date) & 
                (messages_df['Timestamp'] < period_end)
            ]

            if not period_df.empty:
                logging.info(f"Found {len(period_df)} messages in period")
                
                # Generate summaries directly
                summaries = summary_generator.generate_summary(
                    period_df, days_per_summary
                )
                if summaries:
                    discord_summary, _, reddit_summary = summaries
                    # Learn from summaries
                    if discord_summary:
                        project_manager.learn_from_summary(discord_summary)
                        logging.info("Learned from Discord summary")
                    if reddit_summary:
                        project_manager.learn_from_summary(reddit_summary)
                        logging.info("Learned from Reddit summary")

            current_date = period_end

    except Exception as e:
        logging.error(f"Error processing exports: {e}", exc_info=True)
        raise

def main():
    """Build knowledge base from historical Discord data."""
    setup_logging()
    logging.info("Starting knowledge base build from historical data")

    try:
        # First, run the export script for development channel
        export_script = Path(__file__).parent / 'export_channel.sh'
        try:
            # Export development channel (669989266478202917) for 365 days
            subprocess.run(['bash', str(export_script), '669989266478202917', '365'], check=True)
            logging.info("Successfully exported historical data")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to export historical data: {e}")
            sys.exit(1)

        # Process the exports
        process_exports()
        logging.info("Successfully built knowledge base from historical data")

    except Exception as e:
        logging.error(f"Failed to build knowledge base: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
