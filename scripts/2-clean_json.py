import os
import json
import glob
import re
from datetime import datetime
import argparse
from dotenv import load_dotenv
from collections import Counter
import csv

# Load environment variables from .env file
load_dotenv()

# Configuration Variables
CHANNEL_ID_REGEX = os.getenv("CHANNEL_ID_REGEX", r'\[(\d+)\]')

# Function to get all .json files based on modified date in the first folder of output* folder or from input argument
def get_all_json_files(input_dir=None):
    if input_dir:
        print(f"Looking for JSON files in provided input directory: {input_dir}")
        json_files = glob.glob(os.path.join(input_dir, '**', '*.json'), recursive=True)
    else:
        output_folders = sorted([d for d in glob.glob('output*/') if os.path.isdir(d)], key=os.path.getmtime)
        if not output_folders:
            raise FileNotFoundError("No folders found in 'output/' directory.")
        for folder in output_folders:
            print(f"Looking for JSON files in folder by modified date: {folder}")
            json_files = glob.glob(os.path.join(folder, '**', '*.json'), recursive=True)
            json_files = [f for f in json_files if 'cleaned_chatlog.json' not in f]
            if json_files:
                break
        else:
            raise FileNotFoundError("No JSON files found in any 'output/' folder.")
    
    print(f"Found {len(json_files)} JSON files.")
    return json_files, folder if not input_dir else input_dir

# Function to clean the json data and keep only necessary fields
def clean_chatlog_data(data):
    if not isinstance(data, dict) or 'messages' not in data:
        raise ValueError("Invalid JSON structure: expected a dictionary with a 'messages' key.")

    cleaned_messages = []
    
    for message in data.get('messages', []):
        if not isinstance(message, dict):
            continue
        cleaned_message = {
            'guild_id': data.get('guild', {}).get('id', 'Unknown'),
            'channel_id': data.get('channel', {}).get('id', 'Unknown'),
            'channel_category': data.get('channel', {}).get('category', 'Unknown'),
            'channel_name': data.get('channel', {}).get('name', 'Unknown').strip(),
            'message_id': message.get('id', 'Unknown'),
            'message_content': message.get('content', ''),
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

# Function to save cleaned data to a new json file
def save_cleaned_data(cleaned_data, output_dir, output_file='json_cleaned.json'):
    output_path = os.path.join(output_dir, output_file)
    print(f"Saving cleaned data to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(cleaned_data, f, indent=4)

# Function to save cleaned data to CSV file
def save_cleaned_data_to_csv(cleaned_data, output_dir, output_file='json_cleaned.csv'):
    output_path = os.path.join(output_dir, output_file)
    print(f"Saving cleaned data to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'guild_id', 'channel_id', 'channel_category', 'channel_name', 
            'message_id', 'message_content', 'message_timestamp', 
            'message_reactions', 'message_mentions', 'author_id', 
            'author_name', 'author_nickname', 'role_position'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for message in cleaned_data:
            row = {
                'guild_id': message['guild_id'],
                'channel_id': message['channel_id'],
                'channel_category': message['channel_category'],
                'channel_name': message['channel_name'],
                'message_id': message['message_id'],
                'message_content': message['message_content'],
                'message_timestamp': message['message_timestamp'],
                'message_reactions': json.dumps(message['message_reactions']),
                'message_mentions': json.dumps(message['message_mentions']),
                'author_id': message['author_id'],
                'author_name': message['author_name'],
                'author_nickname': message['author_nickname'],
                'role_position': json.dumps(message['role_position'])
            }
            print(f"Writing row to CSV: {row}")  # Logging each row before writing
            writer.writerow(row)

# Function to print stats about the cleaned data
def print_stats(cleaned_data):
    total_messages = len(cleaned_data)
    authors = [message['author_name'] for message in cleaned_data if message['author_name']]
    channel_names = [message['channel_name'] for message in cleaned_data if message['channel_name']]
    
    author_counter = Counter(authors)
    channel_counter = Counter(channel_names)
    
    print(f"\n--- Stats ---")
    print(f"Total messages: {total_messages}")
    print(f"Number of unique authors: {len(author_counter)}")
    print("Top 5 most active authors:")
    for author, count in author_counter.most_common(5):
        print(f"  {author}: {count} messages")
    print(f"Number of unique channels: {len(channel_counter)}")
    print("Top 5 most active channels:")
    for channel, count in channel_counter.most_common(5):
        print(f"  {channel}: {count} messages")

# Main function to execute the cleaning process
def main():
    # Parse input directory argument
    parser = argparse.ArgumentParser(description="Clean chat logs JSON")
    parser.add_argument('--input-dir', type=str, help="Directory containing the exported JSON chat logs")
    args = parser.parse_args()

    try:
        json_files, first_folder = get_all_json_files(args.input_dir)
        
    except FileNotFoundError as e:
        print(e)
        return

    all_cleaned_data = []
    error_log = []
    
    for json_file in json_files:
        print(f"Processing JSON file: {json_file}")
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            cleaned_data = clean_chatlog_data(data)
            print(f"Cleaned data from {json_file}: {cleaned_data}")  # Logging cleaned data
            all_cleaned_data.extend(cleaned_data)
        except (json.JSONDecodeError, ValueError) as e:
            error_message = f"Error decoding JSON file {json_file}: {e}"
            print(error_message)
            error_log.append(error_message)
        except Exception as e:
            error_message = f"Unexpected error with file {json_file}: {e}"
            print(error_message)
            error_log.append(error_message)

    if not all_cleaned_data and json_files:
        print("No valid JSON data found in the current files.")
        return

    if all_cleaned_data:
        # Determine the output directory based on each JSON file being processed
        output_dir = os.path.dirname(json_files[0])
        
        save_cleaned_data(all_cleaned_data, output_dir)
        save_cleaned_data_to_csv(all_cleaned_data, output_dir)
        print(f"Cleaned data saved to {os.path.join(output_dir, 'cleaned_chatlog.json')} and CSV.")
        
        # Print stats about the cleaned data
        print_stats(all_cleaned_data)
    else:
        print("No valid JSON data found to process.")
    
    if error_log:
        error_log_path = os.path.join(output_dir, 'error_log.txt')
        with open(error_log_path, 'w') as error_file:
            error_file.write("\n".join(error_log))
        print(f"Error log saved to {error_log_path}")

if __name__ == "__main__":
    main()