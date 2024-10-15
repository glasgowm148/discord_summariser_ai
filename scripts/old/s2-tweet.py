
import os
import openai
import re
import requests
import pandas as pd
from requests_oauthlib import OAuth1
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# === SECTION 1: Environment Setup ===
load_dotenv()

# Set the OpenAI API key and Twitter API keys from environment variables
api_key = os.getenv("OPENAI_API_KEY")
consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")
if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
    raise ValueError("Twitter API keys are not set.")
if not discord_webhook_url:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is not set.")

openai.api_key = api_key

# === SECTION 2: Load the Latest CSV File ===
def load_latest_csv(directory_path):
    print("Identifying the latest directory...")
    directories = [d for d in Path(directory_path).iterdir() if d.is_dir()]
    if not directories:
        raise FileNotFoundError("No directories found in the output directory.")
    latest_directory = max(directories, key=lambda x: x.stat().st_mtime)
    print(f"Latest directory identified: {latest_directory}")

    print("Searching for the latest cleaned CSV file...")
    cleaned_csv_files = list(latest_directory.glob("combined_cleaned.csv"))
    if not cleaned_csv_files:
        raise FileNotFoundError("No cleaned CSV files found in the latest directory.")
    latest_file = cleaned_csv_files[0]
    print(f"Latest cleaned CSV file found: {latest_file}")

    print("Reading the CSV file...")
    try:
        df = pd.read_csv(latest_file)
        print(f"CSV file read successfully: {latest_file}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        raise
    return df, latest_directory



# === SECTION 3B: Prepare Tweet Content with Timeframe ===
def prepare_tweet_content_with_timeframe(df):
    timeframe_intro = "Ergo Community Highlights from the past 24 hours:\n"
    key_contributors = ['Kushti', 'Armeanio']  # List of key contributors

    # Normalize author names for case-insensitive matching and remove any tags after '#'
    df['author_normalized'] = df['author'].str.split('#').str[0].str.lower()
    key_contributors_normalized = [name.lower() for name in key_contributors]

    # Filter messages from key contributors
    df_key = df[df['author_normalized'].isin(key_contributors_normalized)]

    # Get messages from others
    df_others = df[~df['author_normalized'].isin(key_contributors_normalized)]

    # Collect content data, starting with messages from key contributors
    content_data = []

    # Messages from key contributors
    for _, row in df_key.iterrows():
        author = row['author']
        msg = row['msg']
        timestamp = row['timestamp']
        content_data.append(f"{author} ({timestamp}): {msg}")

    # Messages from other contributors
    for _, row in df_others.iterrows():
        author = row['author']
        msg = row['msg']
        timestamp = row['timestamp']
        content_data.append(f"{author} ({timestamp}): {msg}")

    # Limit the total number of messages to avoid exceeding token limits
    max_messages = 10000  # Adjust as needed
    content_data = content_data[:max_messages]

    if not content_data:
        raise ValueError("No relevant data to summarize.")

    # Join all entries to form a single input string for summarization
    return timeframe_intro + "\n".join(content_data)

# === SECTION 4: Generate a Tweet Summary with GPT-4 ===
def generate_tweet(content):
    system_prompt = (
        "You are an assistant creating a concise, focused summary from a CSV of Discord messages. "
        "Summaries should highlight recent actionable developments in the Ergo ecosystem"
        "Look at discussions by channel_id and time and try and piece together the full conversation."
        "Omit token requests, migration topics, and unrelated projects"
        "Avoid general mentions of community engagement or collaboration unless tied to a new and specific update. "
        "Ensure each point is clear, actionable, and directly relevant to Ergo’s current advancements."
    )

    tweet_prompt = (
        "Summarize the last 24 hours of Discord messages into 9-10 bullet points, each focusing exclusively on specific, actionable updates about Ergo’s technical progress and community projects. "
        "(relevant emoji) [Brief description of the update]: [More details, if needed] (URL, if applicable)"
        "Exclude topics related to token requests, migration, moderation, Rosen, and general community collaboration without specific context. "
        "Use concise language and incorporate engaging emojis, including only points that reflect recent, tangible developments within Ergo's ecosystem. "
        "Refrain from speculative language or references to unrelated projects. Each point should be relevant, informative, and free from unnecessary details."
        "Only include verifiable facts and specific details directly from the summaries; avoid generalizations."
        "Break down complex ideas into smaller, straightforward sentences without adding interpretations."
        "Avoid vague terms or embellishments that might introduce uncertainty."
        "Rephrase any technical terms clearly but accurately to ensure comprehension without altering meaning."
        "Double-check all project names, commands, and URLs to prevent inaccuracies.\n\n"
        f"{content}"
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": tweet_prompt}
            ],
            temperature=0.6,
            max_tokens=1500
        )
        tweet_summary = response.model_dump()["choices"][0]["message"]["content"]
        # Remove any notes or meta-commentary from the output
        tweet_summary = re.sub(r'\(Note:.*?\)', '', tweet_summary, flags=re.DOTALL)
        # Convert markdown links to plain text
        tweet_summary = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', tweet_summary)
        # Remove @ symbols
        tweet_summary = tweet_summary.replace('@', '')
        # Remove markdown bold
        tweet_summary = re.sub(r'\*\*(.*?)\*\*', r'\1', tweet_summary)
        # Ensure 'past 24 hours' is included
        if '24' not in tweet_summary.lower():
            tweet_summary = "In the past 24 hours:\n" + tweet_summary
        # Add call to action
        tweet_summary += f"\n\nJoin the discussion on Discord: {os.environ.get('DISCORD_INVITE_LINK')}"
        print("Tweet summary generated successfully.")
        print(f"Generated Tweet Summary:\n{tweet_summary}\n")  # Display the tweet summary
        return tweet_summary.strip()
    except Exception as e:
        print(f"Error generating tweet summary: {e}")
        return None

# === SECTION 5: Post to Discord ===
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

# === SECTION 6: Post Tweet using Twitter API v2 with OAuth 1.0a ===
def post_tweet(tweet):
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)
    payload = {
        "text": tweet
    }
    print("Posting tweet...")
    try:
        response = requests.post(url, auth=auth, json=payload)
        response_data = response.json()
        if response.status_code in (200, 201):
            print("Tweet posted successfully.")
            log_sent_tweet(tweet)  # Log the tweet to sent_tweets.md
        else:
            error_detail = response_data.get('detail') or response_data.get('errors', response_data)
            print(f"Error posting tweet: {error_detail}")
    except Exception as e:
        print(f"Exception while posting tweet: {e}")

# === SECTION 6A: Log Sent Tweets ===
def log_sent_tweet(tweet):
    log_file = Path('sent_tweets.md')
    date_header = f"\n# {datetime.now().strftime('%Y-%m-%d')}\n"
    try:
        if not log_file.exists():
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(date_header)
                f.write(f"- {tweet}\n")
        else:
            with open(log_file, 'r+', encoding='utf-8') as f:
                content = f.read()
                if date_header not in content:
                    f.write(date_header)
                f.write(f"- {tweet}\n")
        print("Tweet logged successfully to sent_tweets.md.")
    except Exception as e:
        print(f"Failed to log tweet: {e}")

# === SECTION 7: Main Execution ===
if __name__ == "__main__":
    print("Starting execution...")
    csv_directory = './output'
    try:
        df, latest_directory = load_latest_csv(csv_directory)
        stats_content = load_sanitization_stats(latest_directory)
    except FileNotFoundError as e:
        print(e)
        exit(1)
    except Exception as e:
        print(f"Unexpected error during execution: {e}")
        exit(1)

    # Prepare the content for the tweet with the timeframe
    print("Preparing tweet content with timeframe...")
    try:
        tweet_content = prepare_tweet_content_with_timeframe(df)
    except ValueError as e:
        print(e)
        exit(1)

    # Generate a single tweet summary
    tweet_summary = generate_tweet(tweet_content)
    if tweet_summary:
        # Post the tweet summary to Discord
        print("Sending tweet summary to Discord...")
        send_to_discord_in_chunks(tweet_summary, discord_webhook_url)

        # Prompt the user if they want to post the tweet
        user_choice = input("Do you want to post the tweet on Twitter? (yes/no): ").strip().lower()
        if user_choice == 'yes':
            post_tweet(tweet_summary)
        else:
            print("Tweet not posted.")
    else:
        print("Tweet generation failed. No tweet posted.")

