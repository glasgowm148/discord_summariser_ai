#!/usr/bin/env python3

import os
import glob
import csv
import re
from bs4 import BeautifulSoup

# Configuration Variables
EXPORT_DIR = "./output"
SANITIZED_OUTPUT_FILE = "sanitized_chat_log.csv"

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

# Function to extract user, message id, channel id, message content, and timestamp in minimal CSV format
def extract_minimal_messages(chat_log):
    soup = BeautifulSoup(chat_log, 'html.parser')
    
    # Find messages, assuming they are within div tags with a data-message-id attribute
    messages = soup.find_all('div', {'data-message-id': True})
    sanitized_messages = []
    last_user = None  # Track the last known user
    channel_id = None  # Initialize channel_id
    cached_parents = {}  # Cache parents with channel-id to avoid repeated lookups
    previous_timestamp = None  # Track the last known timestamp
    
    for message in messages:
        # Extract message ID
        message_id = message['data-message-id']
        
        # Extract or update channel ID
        # Try to get 'data-channel-id' from the message div
        message_channel_id = message.get('data-channel-id')
        if message_channel_id:
            channel_id = message_channel_id
        else:
            # If not found, look for the nearest parent with 'data-channel-id'
            if message in cached_parents:
                channel_id = cached_parents[message]
            else:
                parent_with_channel_id = message.find_parent(attrs={'data-channel-id': True})
                if parent_with_channel_id:
                    channel_id = parent_with_channel_id['data-channel-id']
                    cached_parents[message] = channel_id  # Cache the result to avoid redundant lookups
                else:
                    # If still not found, channel_id remains as last known or default
                    channel_id = "669989266478202917"

        # Extract message text and sanitize
        # Limit extraction to relevant parts to reduce memory usage
        message_text = message.find('div', class_='chatlog__content').get_text().strip() if message.find('div', class_='chatlog__content') else "[No content]"

        # Extract the author from the span with class 'chatlog__author' using the 'title' attribute
        user_tag = message.find('span', class_='chatlog__author')
        if user_tag and 'title' in user_tag.attrs:
            last_user = user_tag['title'].replace('kushti0978', 'kushti')  # Update the last known user
            user = last_user.replace('kushti0978', 'kushti')
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
        
        # Append author (last_user), message, message_id, channel_id, and timestamp to the list
        if sanitized_message != '[No content]' and user.lower() != 'captain hook':
            sanitized_messages.append([user.replace('kushti0978', 'kushti'), sanitized_message, message_id, channel_id, timestamp])
        
    return sanitized_messages

# Find the most recently modified exported file
list_of_files = glob.iglob(f'{EXPORT_DIR}/*.html')
if not list_of_files:
    print("No HTML files found in the export directory.")
    exit(1)

latest_file = max(list_of_files, key=os.path.getmtime, default=None)
if not latest_file:
    print("No HTML files found in the export directory.")
    exit(1)

# Read the exported chat log
with open(latest_file, 'r', encoding='utf-8') as file:
    chat_log = file.read()

# Extract messages in the minimal CSV format
sanitized_messages = extract_minimal_messages(chat_log)

# Write sanitized data to output CSV file
with open(SANITIZED_OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_out:
    writer = csv.writer(f_out)
    # Write the header
    writer.writerow(['author', 'msg', 'msg_id', 'channel_id', 'timestamp'])
    # Write the sanitized messages
    writer.writerows(sanitized_messages)

print(f"Sanitized data saved to {SANITIZED_OUTPUT_FILE}")