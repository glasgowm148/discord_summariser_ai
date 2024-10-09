import os
import openai
import re
import requests
import pandas as pd
from requests_oauthlib import OAuth1
from dotenv import load_dotenv
from pathlib import Path

# === SECTION 1: Environment Setup ===
load_dotenv()

# Set the OpenAI API key and Twitter API keys from environment variables
api_key = os.getenv("OPENAI_API_KEY")
consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

if api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")
if consumer_key is None or consumer_secret is None or access_token is None or access_token_secret is None:
    raise ValueError("Twitter API keys are not set.")

openai.api_key = api_key

# === SECTION 2: Load the Latest CSV File ===
def load_latest_csv(directory_path):
    print("Identifying the latest directory...")
    # Get the latest modified directory under the output path
    directories = [d for d in Path(directory_path).iterdir() if d.is_dir()]
    if not directories:
        raise FileNotFoundError("No directories found in the output directory.")
    latest_directory = max(directories, key=lambda x: x.stat().st_mtime)
    print(f"Latest directory identified: {latest_directory}")

    print("Searching for the latest cleaned CSV file...")
    # Find the _cleaned.csv file inside the latest directory
    cleaned_csv_files = list(latest_directory.glob("*_cleaned.csv"))
    if not cleaned_csv_files:
        raise FileNotFoundError("No cleaned CSV files found in the latest directory.")
    latest_file = cleaned_csv_files[0]
    print(f"Latest cleaned CSV file found: {latest_file}")
    print("Reading the CSV file...")
    try:
        df = pd.read_csv(latest_file)
        print(f"CSV file read successfully: {latest_file}")
    except pd.errors.EmptyDataError:
        print(f"CSV file is empty: {latest_file}")
        raise
    except pd.errors.ParserError:
        print(f"Error parsing CSV file: {latest_file}")
        raise
    except Exception as e:
        print(f"Unexpected error reading CSV file: {e}")
        raise
    return df, latest_directory

# === SECTION 2A: Load Sanitization Stats ===
def load_sanitization_stats(directory):
    print("Loading sanitization stats...")
    stats_file = directory / 'sanitization_stats.txt'
    if not stats_file.exists():
        raise FileNotFoundError("Sanitization stats file not found in the directory.")
    try:
        with open(stats_file, 'r', encoding='utf-8') as file:
            stats_content = file.read()
            print("Sanitization stats loaded successfully.")
    except Exception as e:
        print(f"Unexpected error reading sanitization stats file: {e}")
        raise
    return stats_content

# === SECTION 3: Extract Relevant Content for Tweet ===
def prepare_tweet_content(df, stats_content):
    content_data = []
    for _, row in df.iterrows():
        author = row['author']
        msg = row['msg']
        timestamp = row['timestamp']
        content_data.append(f"{author} ({timestamp}): {msg}")
    
    if not content_data:
        raise ValueError("The selected column is empty. No data to summarize.")
    
    # Join all entries to form a single input string for summarization
    updates_content = "Here are some recent updates:\n" + "\n".join(content_data)
    return updates_content + "\n\n" + stats_content

# === SECTION 3B: Prepare Tweet Content with Timeframe ===
def prepare_tweet_content_with_timeframe(df):
    timeframe_intro = "Ergo Community Highlights from the past 24 hours:\n"
    
    content_data = []
    for _, row in df.iterrows():
        author = row['author']
        msg = row['msg']
        timestamp = row['timestamp']
        content_data.append(f"{author} ({timestamp}): {msg}")
    
    if not content_data:
        raise ValueError("The selected column is empty. No data to summarize.")
    
    # Join all entries to form a single input string for summarization
    return timeframe_intro + "Here are some recent updates:\n" + "\n".join(content_data)

# === SECTION 4: Generate a Tweet Summary with GPT-4 ===
def generate_tweet(content):
    system_prompt = (
        "You are an assistant tasked with creating a factual and engaging technical summary for Twitter based on discussions from Discord. "
        "Ensure the content remains positive, avoiding negative sentiments like price concerns or FUD. "
        "Include links where appropriate, and make sure all information is specific and relevant to the community. "
        "Community members are encouraged to contribute to the Proof-of-Commitment Protocol (#PoCoP) and engage further in community marketing at app.ergone.io"
        "Your goal is to make the updates informative, engaging, and valuable, highlighting key technical insights from notable figures like Kushti and Armeanio."
    )

    tweet_prompt = (
        "Summarize the following community updates in a concise, engaging manner for Twitter. The summary should include at least 10 key points, with relevant emojis to enhance readability and engagement. "
        "Focus on significant community updates, particularly highlighting technical discussions from key contributors such as Kushti and Armeanio. "
        "Avoid vague language and ensure each point is specific and captures the audience's attention in a straightforward manner.\n"
        f"{content}"
    )

    # Generating tweet summary...
    for attempt in range(3):  # Retry up to 3 times if "24 hours" is missing
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": tweet_prompt}
                ],
                temperature=0.6,
                max_tokens=1000
            )
            tweet_summary = response.model_dump()["choices"][0]["message"]["content"]
            tweet_summary = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', tweet_summary)  # Convert markdown links to Twitter format
            tweet_summary = re.sub(r'@', '', tweet_summary)  # Remove @ symbol but keep username  # Remove @ mentions
            tweet_summary = re.sub(r'\*\*(.*?)\*\*', r'\1', tweet_summary)  # Remove markdown bold (**)
            tweet_summary += f"\n\nJoin the discussion on Discord: {os.environ.get('DISCORD_INVITE_LINK')}"
            print("Tweet summary generated successfully.")
            return tweet_summary
        except Exception as e:
            print(f"Error generating tweet summary: {e}")
    print("Failed to generate a tweet summary after 3 attempts.")
    return None

# === SECTION 5: Post Tweet using Twitter API v2 with OAuth 1.0a ===
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
        else:
            print(f"Error posting tweet: {response_data['detail'] if 'detail' in response_data else response_data}")
    except Exception as e:
        print(f"Exception while posting tweet: {e}")

# === SECTION 6: Main Execution ===
if __name__ == "__main__":
    
    print("Exporting and sanitising messages from the past day...")
    #os.system("./export_chat.sh 1d server")
    # Load the latest CSV file
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
    # Preparing tweet content with timeframe...
    print("Preparing tweet content with timeframe...")
    try:
        tweet_content = prepare_tweet_content_with_timeframe(df)
        tweet_content_with_stats = prepare_tweet_content(df, stats_content)
    except ValueError as e:
        print(e)
        exit(1)

    # Generate multiple tweet summaries
    tweet_summaries = []
    while len(tweet_summaries) < 5:
        tweet_summary = generate_tweet(tweet_content)
        if tweet_summary:
            tweet_summaries.append(tweet_summary)
        else:
            print("Tweet summary not suitable. Attempting to generate another...")
    
    # Let the user pick the best tweet summary to post
    if tweet_summaries:
        for i, summary in enumerate(tweet_summaries, 1):
            print(f"Generated Tweet Summary {i}:{summary}")
        while True:
            try:
                user_choice = int(input("Enter the number of the tweet summary you want to post (1-5): "))
                if 1 <= user_choice <= len(tweet_summaries):
                    post_tweet(tweet_summaries[user_choice - 1])
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 5.")
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 5.")
    else:
        print("Tweet generation failed. No tweet posted.")