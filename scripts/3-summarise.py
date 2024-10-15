# summarise.py
import os
import time
from dotenv import load_dotenv
from functions.load_latest_csv import load_latest_csv
from functions.prepare_summary_content import prepare_summary_content
from functions.generate_summary import generate_summary
from functions.send_to_discord_weekly import send_to_discord_weekly
from functions.send_to_discord_daily import send_to_discord_daily
from functions.send_to_twitter import send_to_twitter

# === SECTION 1: Environment Setup ===
load_dotenv()

# Set API keys from environment variables
api_key = os.getenv("OPENAI_API_KEY")
consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
discord_webhook_url_chinese = os.getenv("DISCORD_WEBHOOK_URL_CHINESE")
discord_webhook_url_spanih = os.getenv("DISCORD_WEBHOOK_URL_SPANISH")
discord_webhook_url_french = os.getenv("DISCORD_WEBHOOK_URL_FRENCH")
discord_webhook_url_turkish = os.getenv("DISCORD_WEBHOOK_URL_TURKISH")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")
if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
    raise ValueError("Twitter API keys are not set.")
if not discord_webhook_url:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is not set.")

# === SECTION 6: Main Execution ===
if __name__ == "__main__":
    print("Starting execution...")
    csv_directory = './output'
    try:
        # Load the latest CSV file
        df, latest_directory, days_covered = load_latest_csv(csv_directory)
    except FileNotFoundError as e:
        print(e)
        exit(1)
    except Exception as e:
        print(f"Unexpected error during execution: {e}")
        exit(1)

    # Prepare the content for the summary with the timeframe
    print("Preparing summary content with timeframe...")
    try:
        summary_content = prepare_summary_content(df)
    except ValueError as e:
        print(e)
        exit(1)

    # Generate a summary (includes logging)
    summary, summary_with_call_to_action = generate_summary(summary_content, days_covered)

    # Check if the summary is valid
    if summary:
        print(f"\nGenerated Summary:\n{summary}\n")
        # Post the summary and translation to Discord
        if days_covered > 5:
            send_to_discord_weekly(summary)
        else:
            send_to_discord_daily(summary)
        # Prompt user to post to Twitter
        user_choice = input("Do you want to send this summary to Twitter? (yes/no): ").strip().lower()
        if user_choice == 'yes':
            send_to_twitter(summary_with_call_to_action)
        else:
            print("Summary not sent to Twitter.")
    else:
        print("Summary generation failed. No summary sent.")
