import os
import discord
from discord.ext import commands
import requests
import asyncio
from pathlib import Path
from openai import OpenAI

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parents[2] / "config" / ".env"
load_dotenv(ENV_PATH)

# Debugging: Print the current working directory
print(f"[DEBUG] Current working directory: {os.getcwd()}")

# Validate required environment variables
required_vars = ["OPENAI_API_KEY", "DISCORD_BOT_TOKEN", "ANNOUNCEMENT_CHANNEL_ID"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    exit(1)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Define bot intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Ensure privileged intent is enabled

bot = commands.Bot(command_prefix="!", intents=intents)

# Webhook URLs for regional channels
webhook_urls = {
    'Russian': os.getenv('DISCORD_WEBHOOK_URL_RUSSIAN'),
    
    'Spanish': os.getenv('DISCORD_WEBHOOK_URL_SPANISH'),
    'Turkish': os.getenv('DISCORD_WEBHOOK_URL_TURKISH'),
    'Indonesian': os.getenv('DISCORD_WEBHOOK_URL_INDONESIAN'),
    'Italian': os.getenv('DISCORD_WEBHOOK_URL_ITALIAN'),
    'German': os.getenv('DISCORD_WEBHOOK_URL_GERMAN'),
    'Portuguese': os.getenv('DISCORD_WEBHOOK_URL_PORTUGUESE'),
    'Japanese': os.getenv('DISCORD_WEBHOOK_URL_JAPANESE'),
    'Korean': os.getenv('DISCORD_WEBHOOK_URL_KOREAN'),
    'Arabic': os.getenv('DISCORD_WEBHOOK_URL_ARABIC'),
    'French': os.getenv('DISCORD_WEBHOOK_URL_FRENCH'),
    'Chinese': os.getenv('DISCORD_WEBHOOK_URL_CHINESE'),
    'Vietnamese': os.getenv('DISCORD_WEBHOOK_URL_VIETNAMESE'),
    'Serbian': os.getenv('DISCORD_WEBHOOK_URL_BALKANS')

}

# Check if any webhook URLs are configured
configured_webhooks = {lang: url for lang, url in webhook_urls.items() if url}
if not configured_webhooks:
    print("[WARNING] No webhook URLs configured! Check your .env file.")
else:
    print(f"[INFO] Configured webhooks for: {', '.join(configured_webhooks.keys())}")

# Hard-coded Channel ID for #announcement
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("ANNOUNCEMENT_CHANNEL_ID"))

# Initialize OpenAI API key


class Translator:
    def __init__(self):
        print("[INFO] Initializing OpenAI client...")
        self.language_map = {
            'Chinese': 'zh', 'Spanish': 'es', 'French': 'fr', 'Turkish': 'tr', 'Russian': 'ru',
            'Indonesian': 'id', 'Italian': 'it', 'German': 'de', 'Portuguese': 'pt',
            'Japanese': 'ja', 'Korean': 'ko', 'Arabic': 'ar'
        }
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    async def translate_content(self, content: str, language: str) -> str:
        """Translate content to specified language using OpenAI."""
        lang_code = self.language_map.get(language, language)
        #print(f"[TRANSLATION] Requesting OpenAI translation for {language})# ({lang_code})...")

        retries = 0
        while retries < self.max_retries:
            try:
                # Construct a more explicit translation prompt
                system_message = f"You are a helpful assistant. Translate the following text to {lang_code}."
                user_message = content
                #print(f"[TRANSLATION] Constructed system message: {system_message}")
                #print(f"[TRANSLATION] User message: {user_message}")

                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
                
                # Make the request to the OpenAI API
                response = client.chat.completions.create(
                    model="gpt-4o",  # Ensure to use the correct GPT-4o model
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1500
                )
                
                # Print the full response to check the model's output
               # print(f"[TRANSLATION] OpenAI response: {response}")
                
                # Ensure we have a valid response content
                if not response or not response.choices:
                    print(f"[ERROR] Invalid response received from OpenAI for {language}!")
                    return content

                # Access the translated content correctly
                translated_text = response.choices[0].message.content.strip()  # Correct way to access translated content
               # print(f"[TRANSLATION] Successfully translated to {language}: {translated_text}")
                return translated_text
                
            except Exception as e:
                print(f"[ERROR] Error translating content to {language}: {str(e)}")
                return content
                
        print(f"[ERROR] Failed to translate to {language} after {self.max_retries} attempts")
        return content






async def send_webhook(url, content, language, max_retries=3):
    """Send a message to a webhook with retry logic and chunking if content is too long."""
    MAX_MESSAGE_LENGTH = 2000  # Discord's max message length
    retries = 0

    # Check if the content is too long, and split it into chunks
    if len(content) > MAX_MESSAGE_LENGTH:
        print(f"[INFO] Content exceeds {MAX_MESSAGE_LENGTH} characters. Splitting into chunks...")
        # Split the content into chunks of MAX_MESSAGE_LENGTH
        chunks = [content[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(content), MAX_MESSAGE_LENGTH)]
    else:
        chunks = [content]  # No need to split if the content is already under the limit

    # Iterate over each chunk
    for chunk in chunks:
        while retries < max_retries:
            try:
                # Send each chunk of content
                data = {"content": chunk}
                response = requests.post(url, json=data, timeout=10)

                if response.status_code >= 200 and response.status_code < 300:
                    print(f"[WEBHOOK] Posted to {language} channel, response: {response.status_code}")
                    return True
                else:
                    print(f"[ERROR] Failed to post to {language} webhook. Status: {response.status_code}, Response: {response.text}")

            except requests.RequestException as e:
                print(f"[ERROR] Request exception when posting to {language} webhook: {str(e)}")

            retries += 1
            if retries < max_retries:
                # Add a small delay before retrying to prevent blocking the heartbeat
                print(f"[INFO] Retrying webhook for {language} in 3 seconds (attempt {retries}/{max_retries})")
                await asyncio.sleep(3)  # Adding a pause here before retrying to avoid blocking

        print(f"[ERROR] Failed to send webhook for {language} after {max_retries} attempts")
    
    return False





translator = Translator()

@bot.event
async def on_ready():
    print(f'[BOT] Logged in as {bot.user}')
    print(f'[BOT] Monitoring announcement channel ID: {ANNOUNCEMENT_CHANNEL_ID}')

@bot.event
async def on_message(message):
    print(f'[MESSAGE] Received in channel {message.channel.id}: {message.content[:50]}{"..." if len(message.content) > 50 else ""}')
    
    if message.channel.id != ANNOUNCEMENT_CHANNEL_ID:
        return
    
    if message.author.bot:
        print("[IGNORE] Message is from a bot, ignoring.")
        return
    
    if not message.content.strip():
        print("[IGNORE] Skipping empty message.")
        return
    
    print(f'[PROCESS] Processing message from #announcement')
    original_text = message.content
    
    # Filter out only configured webhooks
    active_webhooks = {lang: url for lang, url in webhook_urls.items() if url}
    
    if not active_webhooks:
        print("[WARNING] No active webhooks configured, cannot translate messages")
        return
        
    for lang, webhook_url in active_webhooks.items():
        print(f'[TRANSLATION] Translating message to {lang}')
        try:
            translated_text = await translator.translate_content(original_text, lang)
            if translated_text != original_text:  # Only send if translation was successful
                await send_webhook(webhook_url, translated_text, lang)
            else:
                print(f'[WARNING] Translation to {lang} returned original text, possible failure')
        except Exception as e:
            print(f'[ERROR] Unhandled exception processing {lang} translation: {str(e)}')

# Run bot
if __name__ == "__main__":
    print("[BOT] Starting Discord bot...")
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
