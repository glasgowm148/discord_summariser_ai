import os
import glob
import csv
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from collections import Counter, defaultdict

# Load environment variables from .env file
load_dotenv()

# Configuration Variables
EXPORT_DIR = os.getenv("EXPORT_DIR")
print(f"Export directory set to: {EXPORT_DIR}")  # Directory containing exported chat logs, set in .env file
USER_ALIAS = os.getenv("USER_ALIAS")  # Comma-separated list of username alias mappings (e.g., 'original1=alias1,original2=alias2'), set in .env file

# Function to sanitize the message content by removing line breaks, trimming spaces, and removing duplicate bot tags
def sanitize_message(message_text, author):
    # Remove any 'username BOT' that appears duplicated in the message
    bot_pattern = fr"{author} BOT"
    sanitized_text = re.sub(bot_pattern, "", message_text, flags=re.IGNORECASE).strip()

    # Remove line breaks, extra spaces, and dates/times in a single regex operation
    sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()  # Replace multiple spaces or line breaks with a single space
    sanitized_text = re.sub(r'\d+/\d+/\d+\s\d+:\d+\s[APM]{2}', '', sanitized_text)  # Remove dates and times

    # Ensure message is not empty after sanitization
    if not sanitized_text:
        sanitized_text = "[No meaningful content]"
    
    return sanitized_text

# Function to extract the first @username from a forwarded message if the author is missing
def extract_username_from_message(message_text):
    # Regex to find the first instance of @username
    match = re.search(r'@([\w_]+)', message_text)
    if match:
        return match.group(1)
    return "Unknown User"

# Function to extract the timestamp from the message text if the timestamp is missing
def extract_timestamp_from_message_text(message_text):
    # Regex to find the date and time in the message text, accommodating for more variations in timestamp formats
    match = re.search(r'((\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}:\d{2}\s*[APM]{2}))', message_text)
    if match:
        return match.group(1)
    # Additional regex to capture other timestamp formats, e.g., ISO format or different delimiters
    match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)', message_text)
    if match:
        return match.group(1)
    return "Unknown Time"

# Function to apply user alias replacements
def replace_user_alias(user):
    user_alias_dict = dict(alias.split('=') for alias in USER_ALIAS.split(','))
    return user_alias_dict.get(user, user)

# Function to extract user, message id, channel id, message content, and timestamp in minimal CSV format
def extract_minimal_messages(chat_log, channel_id_from_filename, channel_name):
    soup = BeautifulSoup(chat_log, 'html.parser')
    
    # Find messages, assuming they are within div tags with a data-message-id attribute
    messages = soup.find_all('div', {'data-message-id': True})
    sanitized_messages = []
    last_user = None  # Track the last known user
    channel_id = channel_id_from_filename  # Initialize channel_id from filename
    cached_parents = {}  # Cache parents with channel-id to avoid repeated lookups
    previous_timestamp = None  # Track the last known timestamp
    
    for message in messages:
        # Extract message ID
        message_id = message['data-message-id']
        
        # Extract message text and sanitize
        message_text = message.find('div', class_='chatlog__content').get_text().strip() if message.find('div', class_='chatlog__content') else "[No content]"

        # Extract the author from the span with class 'chatlog__author' using the 'title' attribute
        user_tag = message.find('span', class_='chatlog__author')
        if user_tag and 'title' in user_tag.attrs:
            last_user = replace_user_alias(user_tag['title'])  # Update the last known user
            user = last_user
        elif last_user:
            # If there's no user in the current message but we have a known last user, use it
            user = last_user
        else:
            # If author is missing and no last known user, try to extract username from message
            user = extract_username_from_message(message_text)
            last_user = user  # Set this user as the last known user

        # Extract timestamp from the span with class 'chatlog__timestamp'
        timestamp_tag = message.find('span', class_='chatlog__timestamp')
        if timestamp_tag:
            timestamp = timestamp_tag.get_text().strip()
            previous_timestamp = timestamp  # Update the last known timestamp
        else:
            # If timestamp is missing, use the previous known timestamp
            timestamp = previous_timestamp if previous_timestamp else extract_timestamp_from_message_text(message_text)

        # Sanitize the message text
        sanitized_message = sanitize_message(message_text, user)
        
        # Append author (last_user), message, message_id, channel_id, channel_name, and timestamp to the list
        if sanitized_message != '[No content]' and user.lower() != 'captain hook':
            sanitized_messages.append([user, sanitized_message, message_id, channel_id, channel_name, timestamp])
        
    return sanitized_messages

# Find the most recently modified exported folder
list_of_dirs = glob.glob(os.path.join(EXPORT_DIR, '*'))
list_of_dirs = [d for d in list_of_dirs if os.path.isdir(d) and not d.endswith('html_Files')]  # Skip directories ending with 'html_Files'
list_of_dirs = [d for d in list_of_dirs if os.path.isdir(d)]  # Ensure we only get directories
if not list_of_dirs:
    print("No export directories found in the output directory.")
    exit(1)

latest_dir = max(list_of_dirs, key=os.path.getmtime, default=None)
if latest_dir:
    print(f"Latest directory found: {latest_dir}")
else:
    print("No export directories found.")
print(f"Latest directory found: {latest_dir}")
print("Scanning directory for HTML files...")
if not latest_dir:
    print("No export directories found in the output directory.")
    exit(1)

# Find all HTML files in the latest directory
list_of_files = glob.glob(os.path.join(latest_dir, '**', '*.html'), recursive=True)
print(f"HTML files found: {list_of_files}")
print("Extracting messages from HTML files...")
print(f"Total HTML files found: {len(list_of_files)}")
if not list_of_files:
    print("No HTML files found in the latest export directory.")
    exit(1)

sanitized_messages = []
# Read each exported chat log and extract messages
for html_file in list_of_files:
    # Extract channel ID and name from the filename
    channel_id_match = re.search(r'\[(\d+)\]', html_file)
    channel_id_from_filename = channel_id_match.group(1) if channel_id_match else None
    channel_name_match = re.search(r'- (.*?) \[', html_file)
    channel_name = channel_name_match.group(1).strip() if channel_name_match else None

    # Fallback if pattern matching failed
    if not channel_id_from_filename or not channel_name:
        # Attempt to extract from different filename format
        channel_id_from_filename = channel_id_from_filename or "Unknown Channel"
        channel_name = channel_name or os.path.splitext(os.path.basename(html_file))[0]

    with open(html_file, 'r', encoding='utf-8') as file:
        chat_log = file.read()
        extracted_messages = extract_minimal_messages(chat_log, channel_id_from_filename, channel_name)
        print(f"Extracted {len(extracted_messages)} messages from {html_file}")
        sanitized_messages.extend(extracted_messages)

# Generate the sanitized output file name based on the latest directory
date_range = os.path.basename(latest_dir).split('_')[-1]
SANITIZED_OUTPUT_FILE = f"sanitized_chat_log_{date_range.strip()}.csv"

# Write sanitized data to output CSV file
# Ensure directory exists before writing the file
# No need to create a directory for the output file
# Saving directly in the current directory
with open(SANITIZED_OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_out:
    writer = csv.writer(f_out)
    # Write the header
    writer.writerow(['author', 'msg', 'msg_id', 'channel_id', 'channel_name', 'timestamp'])
    # Write the sanitized messages
    filtered_messages = [msg for msg in sanitized_messages if len(msg[1]) > 5]
    print(f"Total messages after filtering short messages: {len(filtered_messages)}")
    writer.writerows(filtered_messages)

# Generate stats
channel_counter = Counter([msg[4] for msg in sanitized_messages])
user_counter = Counter([msg[0] for msg in sanitized_messages])
user_character_counter = defaultdict(int)

# Count the total characters per user
for msg in sanitized_messages:
    user_character_counter[msg[0]] += len(msg[1])

# Deduplicate channel names by normalizing their names
normalized_channel_counter = Counter()
for channel, count in channel_counter.items():
    normalized_channel = channel.lower().strip()
    normalized_channel_counter[normalized_channel] += count

most_active_channels = normalized_channel_counter.most_common(5)
most_active_users = user_counter.most_common(5)
most_active_users_by_characters = sorted(user_character_counter.items(), key=lambda x: x[1], reverse=True)[:5]
total_active_channels = len(normalized_channel_counter)

# Print stats
print("\n--- Stats ---")
print(f"Total active channels: {total_active_channels}")
print("5 most active channels:")
for channel, count in most_active_channels:
    print(f"{channel}: {count} messages")

print("\n5 most active users:")
for user, count in most_active_users:
    print(f"{user}: {count} messages")

print("\n5 most active users by character count:")
for user, char_count in most_active_users_by_characters:
    print(f"{user}: {char_count} characters")

print("Processing complete.")