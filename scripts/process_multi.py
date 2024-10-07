#!/usr/bin/env python3

import os
import openai
import requests
import glob
import csv
import re
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configuration Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SUMMARY_PROMPT = os.getenv("SUMMARY_PROMPT")

# Check if essential environment variables are set
def check_env_variables():
    missing_vars = [var for var in ["OPENAI_API_KEY", "DISCORD_WEBHOOK_URL", "SUMMARY_PROMPT"] if not os.getenv(var)]
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
    excluded_users = ["user1"]
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            author = row['author'].lower()
            if author in excluded_users:
                continue
            message = row['msg']
            timestamp = row['timestamp']
            try:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                timestamp = datetime.strptime(timestamp, '%m/%d/%Y %I:%M %p')

            message_link = f"https://discord.com/channels/{os.getenv('DISCORD_SERVER_ID')}/{row['channel_id']}/{row['msg_id']}"
            chat_log.append(f"**@{author}**: [{message}]({message_link})")
    return chat_log

chat_log = read_chat_log(latest_file)
print(f"Total messages collected for summary: {len(chat_log)}")
max_length = 5000  # Set a limit on the number of messages to include
max_tokens = 10000  # Set a limit on the number of tokens for the OpenAI model
chat_log_combined = chat_log[-max_length:]

# Function to generate the summary with chunking
def generate_summary(chat_log):
    print("Generating summary...")
    
    # Step 1: Split the chat log into smaller chunks
    chunk_size = 1500
    chat_chunks = [chat_log[i:i + chunk_size] for i in range(0, len(chat_log), chunk_size)]
    
    all_summaries = []
    
    # Step 2: Generate summaries for each chunk
    for idx, chunk in enumerate(chat_chunks):
        print(f"Processing chunk {idx + 1}/{len(chat_chunks)}...")
        full_prompt = f"{SUMMARY_PROMPT} {' '.join(chunk)}"

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative and engaging assistant, providing lively and interesting summaries of discussions."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.9  # Increased temperature for more creative summaries
        )
        
        response_dict = response.model_dump()
        all_summaries.append(response_dict["choices"][0]["message"]["content"])
    
    # Step 3: Combine all summaries into one
    combined_summary = "\n\n".join(all_summaries)
    
    # Step 4: Clean and finalize
    final_summary = f"## Summary of discussions across all channels:\n\n{combined_summary}"
    print("Generated summary.")
    return final_summary

final_summary = generate_summary(chat_log)

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

send_to_discord(final_summary, DISCORD_WEBHOOK_URL)