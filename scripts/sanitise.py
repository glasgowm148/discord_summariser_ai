import os
import glob
import csv
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from collections import Counter
import time
import argparse

# Load environment variables from .env file
load_dotenv()

# Configuration Variables
USER_ALIAS = os.getenv("USER_ALIAS")
CHANNEL_ID_REGEX = os.getenv("CHANNEL_ID_REGEX", r'\[(\d+)\]')

# Parse the input directory or file argument
parser = argparse.ArgumentParser(description="Sanitize chat logs")
parser.add_argument('--input-dir', type=str, help="Directory or file containing the exported chat logs")
args = parser.parse_args()

# Set the target path from the parsed argument or default to the first folder in 'output/' by last modified date
if args.input_dir:
    target_path = args.input_dir
else:
    output_folders = [d for d in glob.glob(os.path.join('output', '*')) if os.path.isdir(d)]
    if not output_folders:
        exit("No folders found in 'output/' directory.")
    target_path = max(output_folders, key=os.path.getmtime)
    print(f"No --input-dir provided. Defaulting to the most recently modified folder in 'output/': {target_path}")

# Check if the target path is a file or a directory
if os.path.isfile(target_path):
    # Single file mode
    list_of_files = [target_path]
    print(f"Processing single file: {target_path}")
    # Set the output directory to the directory containing the file
    output_directory = os.path.dirname(target_path)
elif os.path.isdir(target_path):
    # Directory mode: Find all HTML files in the target directory and its subdirectories
    list_of_files = glob.glob(os.path.join(target_path, '**', '*.html'), recursive=True)
    if not list_of_files:
        exit("No HTML files found in the target directory.")
    print(f"Processing directory: {target_path}")
    # Set the output directory to the target path
    output_directory = target_path
else:
    exit("Invalid path: Please provide a valid file or directory path.")

# Function to sanitize the message content
def sanitize_message(message_text, author):
    sanitized_text = re.sub(fr"{author} BOT", "", message_text, flags=re.IGNORECASE).strip()
    sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
    sanitized_text = re.sub(r'\d+/\d+/\d+\s\d+:\d+\s[APM]{2}', '', sanitized_text)
    return sanitized_text if sanitized_text else "[No meaningful content]"

# Function to extract the first @username from a forwarded message if the author is missing
def extract_username_from_message(message_text):
    match = re.search(r'@([\w_]+)', message_text)
    return match.group(1) if match else "Unknown User"

# Function to extract timestamp from message text if missing
def extract_timestamp_from_message_text(message_text):
    match = re.search(r'((\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}:\d{2}\s*[APM]{2}))', message_text) or re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)', message_text)
    return match.group(1) if match else "Unknown Time"

# Function to apply user alias replacements
def replace_user_alias(user):
    if USER_ALIAS:
        user_alias_dict = dict(alias.split('=') for alias in USER_ALIAS.split(','))
        return user_alias_dict.get(user, user)
    return user

# Function to extract user, message id, channel id, message content, and timestamp in minimal CSV format
def extract_minimal_messages(chat_log, channel_name):
    soup = BeautifulSoup(chat_log, 'html.parser')
    messages = soup.find_all('div', {'data-message-id': True})
    sanitized_messages = []
    last_user, previous_timestamp = None, None
    channel_id_match = re.search(CHANNEL_ID_REGEX, channel_name)
    channel_id = channel_id_match.group(1) if channel_id_match else "Unknown_Channel_ID"
    channel_name_clean = re.sub(CHANNEL_ID_REGEX, '', channel_name).strip()
    channel_name_clean = re.sub(r'\[.*?\]', '', channel_name_clean).strip()
    
    for message in messages:
        message_id = message['data-message-id']
        message_text = message.find('div', class_='chatlog__content').get_text().strip() if message.find('div', class_='chatlog__content') else "[No content]"
        user_tag = message.find('span', class_='chatlog__author')
        user = replace_user_alias(user_tag['title']) if user_tag and 'title' in user_tag.attrs else (last_user or extract_username_from_message(message_text))
        last_user = user
        timestamp_tag = message.find('span', class_='chatlog__timestamp')
        timestamp = timestamp_tag.get_text().strip() if timestamp_tag else (previous_timestamp or extract_timestamp_from_message_text(message_text))
        previous_timestamp = timestamp
        sanitized_message = sanitize_message(message_text, user)
        if sanitized_message != '[No content]' and user.lower() != 'captain hook':
            sanitized_messages.append([user, sanitized_message, message_id, channel_id, channel_name_clean, timestamp])
    return sanitized_messages

sanitized_messages = []
regional_messages = []
regional_channels = [
    '🇷🇺│russkiye', '🇮🇹│italiana', '🇮🇩│indonesian', '🇻🇳┃vietnam', '🇪🇸│espanol', '🇪🇸│espanol-mining',
    '🌍│regional-channels', '🔊│regional-outreach', '🇦🇪│arabic', '🇦🇺│australia', '🇦🇱│balkans', '🇨🇦│canada', '🇧🇪│belgium',
    '🇨🇭│chinese', '🇩🇰│denmark', '🇩🇪│deutsch', '🇫🇷│francais', '🇮🇳│india', '🇮🇪│ireland', '🇬🇧│uk', '🇺🇸│usa', '🇯🇵│日本語', '🇱🇻│latvia', '🇹🇷│türk',
    '🇰🇷│한국어', '🇬🇷│ελληνικά', '🇲🇽│mexico', '🇳🇱│nederlands', '🇮🇱│עברית', '🇵🇱│polskie', '🇵🇰│pakistan', '🇵🇭│pilipino', '🇵🇹│português',
    '🇷🇴│romania', '🇸🇪│svenska', '🇸🇰│slovakia', '🇸🇮│slovenia', '🇦🇲│armenian'
]

for html_file in list_of_files:
    print(f"Processing file: {html_file}")
    with open(html_file, 'r', encoding='utf-8') as file:
        chat_log = file.read()
        channel_name_match = re.search(r'- (.*?) \[', html_file) or re.search(r'/([^/]+)\.html$', html_file)
        channel_name = channel_name_match.group(1).strip() if channel_name_match else os.path.splitext(os.path.basename(html_file))[0]
        messages = extract_minimal_messages(chat_log, channel_name)
        print(f"Found {len(messages)} messages in {html_file}.")
        for msg in messages:
            if msg[4].lower() in [channel.lower() for channel in regional_channels]:
                regional_messages.append(msg)
            else:
                sanitized_messages.append(msg)

# Write sanitized data to output CSV file
SANITIZED_OUTPUT_FILE = os.path.join(output_directory, 'combined_cleaned.csv')
REGIONAL_OUTPUT_FILE = os.path.join(output_directory, 'regional_cleaned.csv')

with open(SANITIZED_OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(['author', 'msg', 'msg_id', 'channel_id', 'channel_name', 'timestamp'])
    excluded_channels = [
        'ergonauts', 'tabbypos', 'off-topic', 'moderators', 'foundation', 'treasurer', 'kushti', 
        'peperg', 'sig-mining', '🔞│random', 'cyberverse', '❓│support', '🐣│sig-chat',
        'mew-finance', 'greasycex', 'rosen', 'comet', 'spectrum', 'bober', 'ergone', 'ergopad', 'paideia', 'gluon-gold',
        'rosen-port', 'thz-fm', 'blobs-topia', 'dexyusd-core', 'duckpools', 'ergo-ai', 'ergobass', 
        'regional', 'announcements', 'bridge-tester'
    ]
    filtered_messages = [
        msg for msg in sanitized_messages
        if len(msg[1]) > 5 and msg[4].lower() != 'bridge-tester' and msg[0].lower() != 'chat_summary'
        and 'Forwarded from' not in msg[1] and msg[1] != '[No meaningful content]' and len(msg[1]) >= 10
        and msg[4].lower() not in [channel.lower() for channel in excluded_channels]
        and 'ifttt' not in msg[1].lower() and 'ifttt' not in msg[0].lower()
        and 'chat summariser' not in msg[1].lower() and 'chat summariser' not in msg[0].lower()
    ]
    forwarded_count = sum(1 for msg in sanitized_messages if 'Forwarded from' in msg[1])
    excluded_channels_count = sum(1 for msg in sanitized_messages if msg[4].lower() in [channel.lower() for channel in excluded_channels])
    total_dropped = len(sanitized_messages) - len(filtered_messages)
    print(f"Number of messages containing 'Forwarded from': {forwarded_count}")
    print(f"Number of messages from excluded channels: {excluded_channels_count}")
    print(f"Total number of messages dropped: {total_dropped}")
    print(f"Total number of messages in the final CSV: {len(filtered_messages)}")
    writer.writerows(filtered_messages)

# Write regional messages to a separate CSV file
with open(REGIONAL_OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_regional_out:
    writer = csv.writer(f_regional_out)
    writer.writerow(['author', 'msg', 'msg_id', 'channel_id', 'channel_name', 'timestamp'])
    writer.writerows(regional_messages)
    print(f"Total number of regional messages written to the regional CSV: {len(regional_messages)}")

# Generate and print stats
channel_counter = Counter(msg[4] for msg in filtered_messages)
user_counter = Counter(msg[0] for msg in filtered_messages)
user_character_counter = Counter({msg[0]: len(msg[1]) for msg in filtered_messages})

most_active_channels = channel_counter.most_common(10)
all_channels = channel_counter.most_common()
most_active_users = user_counter.most_common(10)
most_active_users_by_characters = user_character_counter.most_common(10)

# Determine the correct directory for saving the stats file
stats_output_directory = output_directory if os.path.isdir(target_path) else os.path.dirname(target_path)
STATS_OUTPUT_FILE = os.path.join(stats_output_directory, 'sanitization_stats.txt')

with open(STATS_OUTPUT_FILE, 'w', encoding='utf-8') as f_stats:
    f_stats.write(f"--- Stats ---\nTotal active channels: {len(channel_counter)}\n")
    f_stats.write("10 most active channels:\n")
    for channel, count in most_active_channels:
        f_stats.write(f"{channel}: {count} messages\n")

    f_stats.write("\nAll channels with message counts:\n")
    for channel, count in all_channels:
        f_stats.write(f"{channel}: {count} messages\n")

    f_stats.write("\n10 most active users:\n")
    for user, count in most_active_users:
        f_stats.write(f"{user}: {count} messages\n")
    f_stats.write("\n10 most active users by character count:\n")
    for user, char_count in most_active_users_by_characters:
        f_stats.write(f"{user}: {char_count} characters\n")

print(f"Processing complete. Sanitized output written to: {SANITIZED_OUTPUT_FILE}")
print(f"Stats output written to: {STATS_OUTPUT_FILE}")