#!/usr/bin/env python3

import os
import openai
import requests
import glob
import csv
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
EXPORT_DIR = os.getenv("EXPORT_DIR", "./")  # Default to "./" if not set
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")

# Check if essential environment variables are set
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is not set in the environment.")
    exit(1)
if not DISCORD_WEBHOOK_URL:
    print("Error: DISCORD_WEBHOOK_URL is not set in the environment.")
    exit(1)
if not DISCORD_SERVER_ID:
    print("Error: DISCORD_SERVER_ID is not set in the environment.")
    exit(1)

# Set your OpenAI API key
openai.api_key = OPENAI_API_KEY


# Find the most recently modified exported CSV file
print("Finding the most recently modified CSV file...")
list_of_files = glob.glob(f'{EXPORT_DIR}/*.csv')
if not list_of_files:
    print("No CSV files found in the export directory.")
    exit(1)

latest_file = max(list_of_files, key=os.path.getmtime)

# Read the exported chat log from the CSV file
print("Reading the exported chat log from the CSV file...")
chat_log = []
with open(latest_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Construct a hyperlink for each message using its message ID and channel ID
        message_link = f"https://discord.com/channels/{DISCORD_SERVER_ID}/{row['channel_id']}/{row['msg_id']}"
        # Add author and hyperlinked message to the log
        chat_log.append(f"**@{row['author']}**: [{row['msg']}]({message_link})")


# Combine chat log into a single string
print("Combining chat log into a single string...")
chat_log_combined = "\n".join(chat_log)

# Function to clean up unnecessary content in the response
def clean_summary(summary):
    # Remove repeated titles or unwanted phrases
    cleaned_summary = summary.replace("Summary of Activities from", "", 1).strip()
    return cleaned_summary

# Function to check if the summary meets the requirements
def check_summary_requirements(summary):
    # Check if the summary contains at least 3 links
    link_pattern = r"https?://\S+"
    links = re.findall(link_pattern, summary)
    # Check if the summary contains more than 3 emojis
    emoji_pattern = re.compile(r'[^\w\s,]', re.UNICODE)
    emojis = emoji_pattern.findall(summary)
    return len(links) >= 3 and len(emojis) > 3

# Prompt for summarization
prompt = """
You are tasked with summarizing the following discussions from the development channel into a concise summary. Your goal is to extract only the most significant and relevant information that would interest the entire community.

Guidelines:

1. Focus on key updates, announcements, new ideas, and significant discussions.
2. Exclude routine messages, personal chats, and less relevant content.
3. Format each point concisely, prefixed with an appropriate emoji.
4. Maintain a neutral and informative tone.
5. Ensure the final summary fits within 2000 characters.
6. Use bullet points and emojis for each item. Use plain text for names, and hyperlink any references to projects or discussions using markdown syntax.
7. Group similar usernames (like 'Kushti0978' and 'kushti') into '@kushti'.
8. Include a hyperlink to the original message using the format '@username [discussion topic](message_link)'.
9. Avoid unnecessary context or phrases like 'hinting at.'
10. Each person (@username) should have only one bullet. If they have multiple points, merge them into one.
11. This covers the last week's chats, so avoid using phrases like 'tomorrow.'

Below are the chat logs:

{chat_logs}
"""


# Function to generate and check the summary
def generate_and_check_summary():
    suitable_summaries = []
    for i in range(15):
        print(f"Attempt {i + 1} to generate a suitable summary...")
        # Combine the prompt with the full chat log
        full_prompt = f"{prompt}\n\n{chat_log_combined}"

        # Send the entire log to OpenAI for summarization, limiting the response to 1500 tokens (to keep it concise)
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt}
            ],
            # max_tokens=1500,
            temperature=0.7
        )

        response_dict = response.model_dump()  # Convert to dictionary
        summary = response_dict["choices"][0]["message"]["content"]  # Access the message

        cleaned_summary = clean_summary(summary)

        # Add the title back only once
        final_summary = f"## Summary of development discussions this week!\n\n{cleaned_summary}"

        # Check if the summary meets the requirements
        if check_summary_requirements(final_summary):
            link_pattern = r"https?://\S+"
            links = re.findall(link_pattern, final_summary)
            emoji_pattern = re.compile(r'[^\w\s,]', re.UNICODE)
            emojis = emoji_pattern.findall(final_summary)
            bullets = final_summary.count('- ')
            print(f"Summary meets requirements with {len(links)} links, {len(emojis)} emojis, and {bullets} bullets.")
            suitable_summaries.append((final_summary, len(links)))
            if len(suitable_summaries) == 5:
                break
        else:
            print(f"Attempt {i + 1}: Summary does not meet requirements.")
            print(final_summary)

    if suitable_summaries:
        print("Picking the suitable summary with the most links...")
        best_summary = max(suitable_summaries, key=lambda x: x[1])[0]
    else:
        print("Failed to generate a suitable summary after 15 attempts.")
        best_summary = "Summary of development discussions this week!\n\n- No suitable summary could be generated."

    return best_summary

# Generate the summary and check if it meets the requirements
print("Generating final summary...")
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
        data = {
            "content": chunk
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(webhook_url, json=data, headers=headers)

        if response.status_code == 204:
            print(f"Chunk {i + 1} sent successfully.")
        else:
            print(f"Failed to send chunk {i + 1}: {response.status_code}")

# Check if the summary is within Discord's character limit
if len(final_summary) > 2000:
    print(f"Summary exceeds 2000 characters, sending in chunks.")
    send_to_discord_in_chunks(final_summary, DISCORD_WEBHOOK_URL)
else:
    print("Sending final summary to Discord...")
    # Send the final summary to Discord in one message
    data = {
        "content": final_summary
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=data, headers=headers)

    if response.status_code == 204:
        print("Summary sent to Discord successfully.")
    else:
        print(f"Failed to send summary to Discord: {response.status_code}")
