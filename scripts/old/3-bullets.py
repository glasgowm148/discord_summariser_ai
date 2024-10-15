#!/usr/bin/env python3

import os
import openai
import requests
import glob
import csv
import re
import time
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configuration Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SUMMARY_PROMPT = os.getenv("SUMMARY_PROMPT")
HACKMD_API_TOKEN = os.getenv("HACKMD_API_TOKEN")

# Check if essential environment variables are set
def check_env_variables():
    missing_vars = [var for var in ["OPENAI_API_KEY", "DISCORD_WEBHOOK_URL", "SUMMARY_PROMPT", "HACKMD_API_TOKEN"] if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
        exit(1)

check_env_variables()

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Find the most recently modified exported CSV file
def get_latest_csv_file():
    csv_files = glob.glob('./output/cleaned/*.csv')
    if not csv_files:
        print("No CSV files found in the specified directory: ./output/cleaned")
        exit(1)
    return max(csv_files, key=os.path.getmtime)

latest_file = get_latest_csv_file()
print(f"Using CSV file: {latest_file}")

# Read the exported chat log from the CSV file
def read_chat_log(csv_file):
    chat_log = []
    print(f"Reading CSV file: {csv_file}")
    excluded_users = ["paul1938", "austenmilbarge", "pulsarz", "pavel"]
    excluded_channels = [
        "baseless-speculation",
        "cyberverse",
        "sig-mining",
        "trading",
        "random",
        "greasycex",
        "mew-finance",
        "sig-chat",
        "rosen"
    ]
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            author = row['author'].lower()
            channel = row['channel_name'].lower()
            if author in excluded_users or channel in excluded_channels:
                continue
            message = row['msg']
            if len(message) > 1000:
                print(f"Warning: Message from {author} may be too long and could get truncated: {message[:50]}...")
            timestamp = row['timestamp']
            try:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                timestamp = datetime.strptime(timestamp, '%m/%d/%Y %I:%M %p')

            message_link = f"https://discord.com/channels/{os.getenv('DISCORD_SERVER_ID')}/{row['channel_id']}/{row['msg_id']}"
            chat_log.append({
                "author": author,
                "message": message,
                "link": message_link,
                "timestamp": timestamp,
                "channel_id": row['channel_id'],
                "msg_id": row['msg_id'],
                "discussion_id": None
            })
    return chat_log

chat_log = read_chat_log(latest_file)
print(f"Total messages collected for summary: {len(chat_log)}")

# Filter relevant messages before summarizing
def filter_relevant_messages(chat_log):
    print("Filtering relevant messages...")
    keywords = ["update", "announcement", "release", "important", "discussion"]
    filtered_log = [msg for msg in chat_log if any(keyword in msg['message'].lower() for keyword in keywords) or msg['author'] in ["kushti", "mgpai", "armeanio"]]
    print(f"Total relevant messages after filtering: {len(filtered_log)}")
    return filtered_log

filtered_chat_log = filter_relevant_messages(chat_log)
max_length = 1000  # Set a limit on the number of messages to include
chat_log_combined = filtered_chat_log[-max_length:]

# Group messages into discussions before summarizing
def group_messages_by_discussion(chat_log, max_tokens=1500):
    discussions = []
    current_discussion = []
    current_token_count = 0

    for msg in chat_log:
        message_token_count = len(msg['message'].split())
        # If adding this message exceeds the max token limit, start a new discussion
        if current_token_count + message_token_count > max_tokens:
            if current_discussion:
                discussions.append(current_discussion)
            current_discussion = [msg]
            current_token_count = message_token_count
        else:
            current_discussion.append(msg)
            current_token_count += message_token_count

    # Append the last discussion if any messages remain
    if current_discussion:
        discussions.append(current_discussion)

    print(f"Total discussions grouped: {len(discussions)}")
    return discussions

grouped_discussions = group_messages_by_discussion(chat_log_combined)

# Add discussion ID to each message
discussion_id = 1
for discussion in grouped_discussions:
    for msg in discussion:
        msg['discussion_id'] = discussion_id
    discussion_id += 1

# Let AI summarize the grouped discussions with error handling
def generate_ai_summary(grouped_discussions):
    print("Generating AI summary...")
    all_summaries = []

    for i, discussion in enumerate(grouped_discussions):
        print(f"Processing discussion {i + 1}/{len(grouped_discussions)}...")
        messages = [f"**@{msg['author']}**: {msg['message']} ({msg['link']})" for msg in discussion]
        for msg in messages:
            if len(msg) > 1500:
                print(f"Warning: A message may be too long and could get truncated: {msg[:50]}...")
        full_prompt = f"{SUMMARY_PROMPT} {' '.join(messages)}"
        if len(full_prompt) > 5000:
            print("Warning: The full prompt length exceeds 5000 characters and might get truncated.")

        retries = 3
        while retries > 0:
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant tasked with summarizing discussions."},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                response_dict = response.model_dump()["choices"][0]["message"]["content"]
                print(f"Received response for discussion {i + 1}.")
                all_summaries.append(response_dict)
                break
            except openai.error.OpenAIError as e:
                print(f"Error occurred: {e}. Retrying... ({retries} retries left)")
                retries -= 1
                time.sleep(5)
        else:
            print(f"Failed to generate summary after multiple retries for discussion {i + 1}. Skipping this discussion.")
    
    return all_summaries

# Extract bullet points from summaries into a dataframe
def extract_bullet_points_to_dataframe(all_summaries):
    bullet_points = []
    for summary in all_summaries:
        bullet_points.extend([line for line in summary.split('\n') if line.startswith('- ') and line.split(':')[-1].strip() != ''])
    df = pd.DataFrame(bullet_points, columns=['Bullet Points'])
    return df

# Main execution
all_summaries = generate_ai_summary(grouped_discussions)
bullet_points_df = extract_bullet_points_to_dataframe(all_summaries)

# Add discussion IDs to bullet points
discussion_ids = []
for i, summary in enumerate(all_summaries):
    bullet_count = len([line for line in summary.split('\n') if line.startswith('- ')])
    discussion_ids.extend([i + 1] * bullet_count)

# Ensure the length of discussion_ids matches the length of bullet_points_df
discussion_ids = discussion_ids[:len(bullet_points_df)]

bullet_points_df['Discussion ID'] = discussion_ids
discussion_ids = bullet_points_df['Discussion ID']

# Display the dataframe to the user
print("Extracted bullet points:")
print(bullet_points_df)

# Export the dataframe to a CSV file
bullet_points_df.to_csv('./output/bullet_points_summary.csv', index=False)
print("Bullet points exported to './output/bullet_points_summary.csv'")

# Generate final summary from reviewed bullet points
def generate_final_summary(reviewed_bullets):
    final_summary = "## Summary of discussions across all channels:\n\n" + "\n".join(reviewed_bullets)
    return final_summary

# Post the summary to HackMD
def post_to_hackmd(content):
    headers = {
        "Authorization": f"Bearer {HACKMD_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "content": content,
        "readPermission": "guest"
    }
    response = requests.post("https://api.hackmd.io/v1/notes", headers=headers, json=data)
    if response.status_code == 200:
        note_url = response.json().get("publishLink")
        print(f"Successfully posted summary to HackMD: {note_url}")
    else:
        print(f"Failed to post summary to HackMD: {response.status_code} - {response.text}")

# Send the final summary to Discord
def send_to_discord(content, webhook_url):
    current_chunk = ""
    chunks = []
    for line in content.split(" "):
        if len(current_chunk) + len(line) + 1 <= 2000:
            current_chunk += line + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = line + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    for i, chunk in enumerate(chunks):
        print(f"Sending chunk {i + 1}/{len(chunks)} to Discord...")
        response = requests.post(webhook_url, json={"content": chunk}, headers={"Content-Type": "application/json"})
        if response.status_code != 204:
            print(f"Failed to send chunk: {response.status_code}")

# Generate and send final summary (if needed)
# reviewed_bullets = [line for line in bullet_points_df['Bullet Points']]  # Example to use all bullet points
# final_summary = generate_final_summary(reviewed_bullets)
# send_to_discord(final_summary, DISCORD_WEBHOOK_URL)
# post_to_hackmd(final_summary)