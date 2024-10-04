#!/usr/bin/env python3

import os
import openai
import requests
import glob
import csv
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Configuration Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
EXPORT_DIR = os.getenv("EXPORT_DIR", "./")  # Default to "./" if not set
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
SUMMARY_PROMPT = os.getenv("SUMMARY_PROMPT")

# Check if essential environment variables are set
def check_env_variables():
    missing_vars = []
    if not OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")
    if not DISCORD_WEBHOOK_URL:
        missing_vars.append("DISCORD_WEBHOOK_URL")
    if not DISCORD_SERVER_ID:
        missing_vars.append("DISCORD_SERVER_ID")
    if not SUMMARY_PROMPT:
        missing_vars.append("SUMMARY_PROMPT")
    if missing_vars:
        print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
        exit(1)

check_env_variables()

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Find the most recently modified exported CSV file
def get_latest_csv_file(directory):
    print("Finding the most recently modified CSV file...")
    list_of_files = glob.glob(f'{directory}/*.csv')
    if not list_of_files:
        print("No CSV files found in the export directory.")
        exit(1)
    return max(list_of_files, key=os.path.getmtime)

latest_file = get_latest_csv_file(EXPORT_DIR)

# Read the exported chat log from the CSV file
def read_chat_log(csv_file, priority_authors):
    print("Reading the exported chat log from the CSV file...")
    chat_log = []
    after_dev_update_call = False
    dev_update_time = None
    dev_update_message_link = None
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            author = row['author'].lower()
            message_link = f"https://discord.com/channels/{DISCORD_SERVER_ID}/{row['channel_id']}/{row['msg_id']}"
            timestamp_str = row['timestamp']
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

            # Check if this message is the dev update call
            if "share your updates" in row['msg'].lower():
                after_dev_update_call = True
                dev_update_time = timestamp
                dev_update_message_link = message_link
                continue

            # Prioritize messages after the dev update call, especially those within a few hours and with bullet points
            if after_dev_update_call and dev_update_time:
                time_diff = timestamp - dev_update_time
                if time_diff <= timedelta(hours=4) and (author in priority_authors or "-" in row['msg'] or "*" in row['msg'] or "important" in row['msg'].lower() or "update" in row['msg'].lower()):
                    chat_log.append(f"**@{row['author']}**: [{row['msg']}]({message_link})")
    return chat_log, dev_update_message_link

PRIORITY_AUTHORS = ["kushti", "mgpai", "cheeseenthusiast", "zargarzadehmoein", "pgr456", "arobsn", "luivatra"]
chat_log, dev_update_message_link = read_chat_log(latest_file, PRIORITY_AUTHORS)

# Combine chat log into a single string
chat_log_combined = "\n".join(chat_log)

# Function to clean up unnecessary content in the response
def clean_summary(summary):
    return summary.replace("Summary of Activities from", "", 1).strip()

# Function to check if the summary meets the requirements
def check_summary_requirements(summary):
    link_pattern = r"https?://\S+"
    links = re.findall(link_pattern, summary)
    return len(links) >= 3

# Function to generate and check the summary
def generate_and_check_summary():
    prompt = SUMMARY_PROMPT.format(chat_logs=chat_log_combined)

    suitable_summaries = []
    for i in range(15):
        print(f"Attempt {i + 1} to generate a suitable summary...")
        full_prompt = f"{prompt}\n\n{chat_log_combined}"

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3
        )

        summary = response['choices'][0]['message']['content']
        cleaned_summary = clean_summary(summary)
        final_summary = f"## Summary of development discussions this week!\n\n{cleaned_summary}\n\n[Link to the start of the weekly dev chat]({dev_update_message_link})"

        if check_summary_requirements(final_summary):
            suitable_summaries.append(final_summary)
            if len(suitable_summaries) == 5:
                break
        else:
            print(f"Attempt {i + 1}: Summary does not meet requirements.")

    if suitable_summaries:
        return max(suitable_summaries, key=lambda x: len(re.findall(r'https?://\S+', x)))
    else:
        return f"Summary of development discussions this week!\n\n- No suitable summary could be generated.\n\n[Link to the start of the weekly dev chat]({dev_update_message_link})"

# Generate the summary
final_summary = generate_and_check_summary()

# Remove linebreaks between bullets in the final summary
final_summary = re.sub(r'\n(?=- )', '', final_summary)

# Function to send messages to Discord in chunks of max 2000 characters
def send_to_discord_in_chunks(content, webhook_url, chunk_size=2000):
    chunks = []
    current_chunk = ""
    for line in content.split("\n"):
        if len(current_chunk) + len(line) + 1 <= chunk_size:
            current_chunk += line + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())

    for i, chunk in enumerate(chunks):
        response = requests.post(webhook_url, json={"content": chunk}, headers={"Content-Type": "application/json"})
        if response.status_code == 204:
            print(f"Chunk {i + 1} sent successfully.")
        else:
            print(f"Failed to send chunk {i + 1}: {response.status_code}")

# Send the final summary to Discord
if len(final_summary) > 2000:
    print(f"Summary exceeds 2000 characters, sending in chunks.")
    send_to_discord_in_chunks(final_summary, DISCORD_WEBHOOK_URL)
else:
    print("Sending final summary to Discord...")
    response = requests.post(DISCORD_WEBHOOK_URL, json={"content": final_summary}, headers={"Content-Type": "application/json"})
    if response.status_code == 204:
        print("Summary sent to Discord successfully.")
    else:
        print(f"Failed to send summary to Discord: {response.status_code}")