# services/json_cleaner.py
import os
import glob
import json
import csv
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv

class JsonCleanerService:
    def __init__(self):
        # Load environment variables from config/.env
        env_path = Path('config/.env')
        if not env_path.exists():
            raise FileNotFoundError("config/.env file not found. Please copy config/.env.example to config/.env and fill in your values.")
        load_dotenv(env_path)
        
        self.channel_id_regex = os.getenv("CHANNEL_ID_REGEX", r'\[(\d+)\]')
        self.excluded_channels = ['bridge-tester', 'greasycex', 'mew-finance']
        self.excluded_categories = [
            'Σ  ・〘 Sigmanauts 〙☰',
            '🗣 ・〘 Discussions 〙☰',
            '🏠  ・〘 INFORMATION 〙☰',
            '🏔 ・〘 Foundation 〙☰',
            '🗺  ・〘 Regional 〙☰'
        ]

    def get_json_files(self, input_dir: str = None) -> Tuple[List[str], str]:
        if input_dir:
            search_dir = input_dir
        else:
            export_dirs = glob.glob('output/export-*')
            if not export_dirs:
                raise FileNotFoundError("No export directories found under 'output/'")
            search_dir = max(export_dirs, key=os.path.getmtime)
        
        json_files = glob.glob(os.path.join(search_dir, '**', '*.json'), recursive=True)
        json_files = [
            f for f in json_files
            if 'cleaned_chatlog.json' not in f and not f.endswith('json_cleaned.json')
        ]
        
        if not json_files:
            raise FileNotFoundError(f"No valid JSON files found in '{search_dir}'")
        
        return json_files, search_dir

    def clean_chatlog_data(self, data: Dict) -> List[Dict]:
        if not isinstance(data, dict) or 'messages' not in data:
            raise ValueError("Invalid JSON structure: expected a dictionary with a 'messages' key.")

        cleaned_messages = []
        
        for message in data.get('messages', []):
            if not isinstance(message, dict):
                continue

            channel_name = data.get('channel', {}).get('name', 'Unknown').strip()
            channel_category = data.get('channel', {}).get('category', 'Unknown').strip()

            if channel_name in self.excluded_channels:
                continue

            if channel_category in self.excluded_categories:
                continue

            message_content = message.get('content', '')
            if (
                len(message_content) < 10 or
                'Forwarded from' in message_content or
                'ifttt' in message_content.lower() or
                'chat summariser' in message_content.lower()
            ):
                continue

            cleaned_message = {
                'channel_id': data.get('channel', {}).get('id', 'Unknown'),
                'channel_category': channel_category,
                'channel_name': channel_name,
                'message_id': message.get('id', 'Unknown'),
                'message_content': message_content,
                'message_timestamp': message.get('timestamp', 'Unknown'),
                'message_reactions': [
                    {
                        'emoji_name': reaction.get('emoji', {}).get('name', 'Unknown'),
                        'count': reaction.get('count', 0)
                    }
                    for reaction in message.get('reactions', []) if isinstance(reaction, dict)
                ],
                'message_mentions': [
                    mention.get('id', 'Unknown') for mention in message.get('mentions', []) if isinstance(mention, dict)
                ],
                'author_id': message.get('author', {}).get('id', 'Unknown'),
                'author_name': message.get('author', {}).get('name', 'Unknown'),
                'author_nickname': message.get('author', {}).get('nickname', 'Unknown'),
                'role_position': [
                    role.get('position', 'Unknown') for role in message.get('author', {}).get('roles', []) if isinstance(role, dict)
                ]
            }
            cleaned_messages.append(cleaned_message)
        
        return cleaned_messages

    def save_json(self, cleaned_data: List[Dict], output_dir: str, output_file: str = 'json_cleaned.json') -> None:
        output_path = os.path.join(output_dir, output_file)
        print(f"Saving cleaned data to {output_path}")
        with open(output_path, 'w') as f:
            # Use separators to remove whitespace and create a compact, single-line JSON
            json.dump(cleaned_data, f, separators=(',', ':'))

    def save_csv(self, cleaned_data: List[Dict], output_dir: str, days_covered: int) -> None:
        """Save cleaned data to CSV with explicit day count in filename."""
        if days_covered <= 0:
            days_covered = self.get_days_covered(cleaned_data)
        
        # Ensure we have a valid number of days
        if days_covered <= 0:
            days_covered = 1  # Default to 1 day if we can't determine the actual count
            
        output_file = f"json_cleaned_{days_covered}d.csv"
        output_path = os.path.join(output_dir, output_file)
        print(f"Saving cleaned data to {output_path} (covering {days_covered} days)")
        
        fieldnames = [
            'channel_id', 'channel_category', 'channel_name', 
            'message_id', 'message_content', 'message_timestamp', 
            'message_reactions_count', 'message_mentions_count', 'author_id', 
            'author_name', 'author_nickname', 'role_position'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for message in cleaned_data:
                row = {
                    'channel_id': message.get('channel_id', 'Unknown'),
                    'channel_category': message.get('channel_category', 'Unknown'),
                    'channel_name': message.get('channel_name', 'Unknown'),
                    'message_id': message.get('message_id', 'Unknown'),
                    'message_content': message.get('message_content', ''),
                    'message_timestamp': message.get('message_timestamp', 'Unknown'),
                    'message_reactions_count': len(message.get('message_reactions', [])),
                    'message_mentions_count': len(message.get('message_mentions', [])),
                    'author_id': message.get('author_id', 'Unknown'),
                    'author_name': message.get('author_name', 'Unknown'),
                    'author_nickname': message.get('author_nickname', 'Unknown'),
                    'role_position': json.dumps(message.get('role_position', []))
                }
                writer.writerow(row)

    def get_days_covered(self, cleaned_data: List[Dict]) -> int:
        """Calculate the number of days covered by the messages."""
        timestamps = []
        for msg in cleaned_data:
            if msg['message_timestamp'] != 'Unknown':
                try:
                    timestamp = datetime.fromisoformat(msg['message_timestamp'])
                    timestamps.append(timestamp)
                except ValueError:
                    print(f"Invalid isoformat string: {msg['message_timestamp']}")
        
        if timestamps:
            min_date = min(timestamps).date()
            max_date = max(timestamps).date()
            days = (max_date - min_date).days + 1
            return max(1, days)  # Ensure at least 1 day
        return 1  # Default to 1 day if no valid timestamps

    def print_stats(self, cleaned_data: List[Dict]) -> None:
        total_messages = len(cleaned_data)
        authors = [message['author_name'] for message in cleaned_data if message['author_name']]
        channel_names = [message['channel_name'] for message in cleaned_data if message['channel_name']]
        
        author_counter = Counter(authors)
        channel_counter = Counter(channel_names)
        
        print("\n--- Stats ---")
        print(f"Total messages: {total_messages}")
        print(f"Number of unique authors: {len(author_counter)}")
        print("Top 5 most active authors:")
        for author, count in author_counter.most_common(5):
            print(f"  {author}: {count} messages")
        print(f"Number of unique channels: {len(channel_counter)}")
        print("Top 5 most active channels:")
        for channel, count in channel_counter.most_common(5):
            print(f"  {channel}: {count} messages")
