# summarise.py
import os
from pathlib import Path
from dotenv import load_dotenv
from services.csv_loader import CsvLoaderService
from services.summary_generator import SummaryGenerator
from services.discord_service import DiscordService
from services.twitter_service import TwitterService

class ChatSummariser:
    def __init__(self):
        # Load environment variables from config/.env
        env_path = Path('config/.env')
        if not env_path.exists():
            raise FileNotFoundError("config/.env file not found. Please copy config/.env.example to config/.env and fill in your values.")
        load_dotenv(env_path)
        
        self._validate_environment()
        
        # Initialize services
        self.csv_loader = CsvLoaderService()
        self.summary_generator = SummaryGenerator(os.getenv("OPENAI_API_KEY"))
        self.discord_service = DiscordService()
        self.twitter_service = TwitterService()

    def _validate_environment(self):
        """Validate that all required environment variables are set."""
        required_vars = {
            "OPENAI_API_KEY": "OpenAI API key",
            "TWITTER_CONSUMER_KEY": "Twitter Consumer Key",
            "TWITTER_CONSUMER_SECRET": "Twitter Consumer Secret",
            "TWITTER_ACCESS_TOKEN": "Twitter Access Token",
            "TWITTER_ACCESS_TOKEN_SECRET": "Twitter Access Token Secret",
            "DISCORD_WEBHOOK_URL": "Discord Webhook URL"
        }
        
        missing_vars = [desc for var, desc in required_vars.items() 
                       if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Validate Discord webhook URL format
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url and not webhook_url.startswith('https://discord.com/api/webhooks/'):
            raise ValueError("DISCORD_WEBHOOK_URL must start with 'https://discord.com/api/webhooks/'")

    def run(self):
        """Execute the main summarization process."""
        print("Starting execution...")
        csv_directory = './output'
        
        try:
            # Load the latest CSV file
            df, latest_directory, days_covered = self.csv_loader.load_latest_csv(csv_directory)
            
            # Generate summary
            print("Generating summary...")
            summary, summary_with_call_to_action = self.summary_generator.generate_summary(df, days_covered)
            
            if not summary:
                print("Summary generation failed. No summary sent.")
                return
            
            print(f"\nGenerated Summary:\n{summary}\n")
            
            # Send to Discord based on days covered
            try:
                print(f"\nAttempting to send to Discord (days covered: {days_covered})...")
                if days_covered > 5:
                    print("Sending as weekly message...")
                    self.discord_service.send_weekly_message(summary)
                else:
                    print("Sending as daily message...")
                    self.discord_service.send_daily_message(summary)
                print("Successfully sent to Discord")
            except Exception as e:
                print(f"\nError sending to Discord: {type(e).__name__}: {str(e)}")
                # Print the summary length for debugging
                print(f"Summary length: {len(summary)} characters")
                # Continue execution to allow Twitter posting even if Discord fails
            
            # Prompt for Twitter posting
            user_choice = input("\nDo you want to send this summary to Twitter? (yes/no): ").strip().lower()
            if user_choice == 'yes':
                try:
                    self.twitter_service.send_tweet(summary_with_call_to_action)
                    print("Successfully sent to Twitter")
                except Exception as e:
                    print(f"Error sending to Twitter: {str(e)}")
            else:
                print("Summary not sent to Twitter.")
                
        except FileNotFoundError as e:
            print(e)
            exit(1)
        except Exception as e:
            print(f"Unexpected error during execution: {type(e).__name__}: {str(e)}")
            exit(1)

if __name__ == "__main__":
    summariser = ChatSummariser()
    summariser.run()
