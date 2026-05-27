import os
import re
import logging
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv
import requests
import sys
import traceback
from pathlib import Path

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Import services
from services.social_media.reddit_service import RedditService
from services.social_media.twitter_service import TwitterService
from utils.logging_config import get_log_path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_log_path('discord_bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordAIBot')

# Load environment variables
load_dotenv(Path(project_root) / 'config' / '.env')

# Configure OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Discord bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
WEBHOOK_CHANNEL_ID = 954383538474614895  # Channel ID where messages will be sent

# Intents configuration
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize services
reddit_service = RedditService()
twitter_service = TwitterService()

def extract_url(text):
    """Extract first URL from text"""
    print(f"[extract_url] ENTRY: text = {text}")

    try:
        url_pattern = r'https?://\S+'
        print(f"[extract_url] Using URL pattern: {url_pattern}")

        match = re.search(url_pattern, text)

        if match:
            url = match.group(0)
            print(f"[extract_url] URL found: {url}")
        else:
            url = None
            print("[extract_url] No URL found in text")

        print(f"[extract_url] EXIT: returning {url}")
        return url

    except Exception as e:
        print(f"[extract_url] EXCEPTION: {e}")
        print(f"[extract_url] Traceback: {traceback.format_exc()}")
        return None

def generate_reddit_title(content, url=None, max_title_length=80):
    """Generate a community-focused, engaging Reddit title"""
    print("TESTWTF2")
    print(f"[generate_reddit_title] ENTRY: content = {content[:100]}, url = {url}")

    try:
        # Truncate content to first 300 characters to prevent overly long context
        truncated_content = content[:300]

        # Determine prompt type
        if url and ('docs' in url or 'documentation' in content.lower()):
            print("[generate_reddit_title] Detected technical documentation context")
            prompt = f"Create a concise, community-engaging title for a technical documentation link. Avoid first-person language. Keep it under {max_title_length} characters. Content context: {truncated_content}"
        else:
            print("[generate_reddit_title] Detected general content context")
            prompt = f"Create a catchy, community-focused title that encourages engagement. Avoid first-person language. Keep it under {max_title_length} characters. Content context: {truncated_content}"

        print(f"[generate_reddit_title] Generated prompt: {prompt}")

        # Generate title using OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Generate a title that sounds like a community post, avoiding personal pronouns. Maximum length is {max_title_length} characters."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50  # Reduced token count to ensure shorter title
        )

        title = response.choices[0].message.content.strip()

        # Remove surrounding quotes and truncate
        title = title.strip('"\'')[:max_title_length]

        print(f"[generate_reddit_title] Generated title: {title}")
        logger.info(f"Generated Reddit title: {title}")

        print(f"[generate_reddit_title] EXIT: returning {title}")
        return title

    except Exception as e:
        print(f"[generate_reddit_title] EXCEPTION: {e}")
        print(f"[generate_reddit_title] Traceback: {traceback.format_exc()}")

        # Fallback title generation
        fallback_title = f"Community Insight: {content[:50]}..." if not url else f"New Resource: {url.split('/')[-1]}"
        fallback_title = fallback_title[:max_title_length]
        print(f"[generate_reddit_title] Fallback title: {fallback_title}")

        return fallback_title

def prepare_reddit_submission(message_content, url=None):
    """Prepare content for Reddit submission"""
    print("TESTWTF3")
    print(f"[prepare_reddit_submission] ENTRY: message_content = {message_content[:100]}, url = {url}")

    try:
        # If URL is present, prepare a link post
        if url:
            print(f"[prepare_reddit_submission] Preparing link post with URL: {url}")
            title = generate_reddit_title(message_content, url)

            submission = {
                'title': title,
                'url': url,
                'selftext': ''  # No additional text for link posts
            }

            print(f"[prepare_reddit_submission] Link post prepared: {submission}")
            return submission

        # For text-based posts
        print("[prepare_reddit_submission] Preparing text-based post")

        # Transform text using OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Transform the text into a community-friendly Reddit post. Remove first-person language, make it sound like a community discussion."},
                {"role": "user", "content": message_content}
            ],
            max_tokens=300
        )

        transformed_text = response.choices[0].message.content.strip()
        print(f"[prepare_reddit_submission] Transformed text: {transformed_text[:200]}...")

        title = generate_reddit_title(message_content)

        submission = {
            'title': title,
            'selftext': transformed_text
        }

        print(f"[prepare_reddit_submission] Text post prepared: {submission}")
        print(f"[prepare_reddit_submission] EXIT: returning submission")
        return submission

    except Exception as e:
        print(f"[prepare_reddit_submission] EXCEPTION: {e}")
        print(f"[prepare_reddit_submission] Traceback: {traceback.format_exc()}")

        # Fallback submission
        fallback_submission = {
            'title': 'Community Discussion',
            'selftext': message_content
        }

        print(f"[prepare_reddit_submission] Fallback submission: {fallback_submission}")
        return fallback_submission

@bot.event
async def on_reaction_add(reaction, user):
    """Handle specific emoji reactions"""
    print(f"[on_reaction_add] ENTRY: reaction = {reaction.emoji}, user = {user.name}")
    print(f"[on_reaction_add] Reaction type: {type(reaction.emoji)}")

    # Ignore bot's own reactions
    if user.bot:
        print("[on_reaction_add] Ignoring bot's own reaction")
        return

    message = reaction.message
    logger.info(f"Reaction added: {reaction.emoji} by {user.name}")

    # Check for custom Reddit emoji
    print(f"[on_reaction_add] Checking emoji: {reaction.emoji}")
    print(f"[on_reaction_add] Emoji name: {getattr(reaction.emoji, 'name', 'No name')}")

    if isinstance(reaction.emoji, discord.PartialEmoji):
        print(f"[on_reaction_add] PartialEmoji detected: {reaction.emoji.name}")

    if isinstance(reaction.emoji, discord.PartialEmoji) and reaction.emoji.name == 'reddit':
        print("[on_reaction_add] Reddit emoji detected")

        # Extract URL if present
        url = extract_url(message.content)
        print(f"[on_reaction_add] Extracted URL: {url}")

        # Generate title
        title = generate_reddit_title(message.content, url)
        print(f"[on_reaction_add] Generated title: {title}")

        # Determine content (URL or message text)
        content = url or message.content
        print(f"[on_reaction_add] Content to post: {content}")

        try:
            print("[on_reaction_add] Attempting to post to Reddit")

            # Post to Reddit
            success = await reddit_service.post_to_reddit(
                title=title,
                content=content
            )

            if success:
                print("[on_reaction_add] Successfully posted to Reddit")
                logger.info("Successfully posted to Reddit")
                await message.add_reaction('✅')
            else:
                print("[on_reaction_add] Failed to post to Reddit")
                logger.error("Failed to post to Reddit")
                await message.add_reaction('❌')

        except Exception as e:
            print(f"[on_reaction_add] Reddit Posting EXCEPTION: {e}")
            print(f"[on_reaction_add] Reddit Posting Traceback: {traceback.format_exc()}")
            logger.error(f"Unexpected error posting to Reddit: {e}")
            logger.error(traceback.format_exc())
            await message.add_reaction('❌')

    # Check for custom Twitter emoji
    elif isinstance(reaction.emoji, discord.PartialEmoji) and reaction.emoji.name == 'twitter':
        print("[on_reaction_add] Twitter emoji detected")
        print(f"[on_reaction_add] Full message content: {message.content}")

        # Extract URL if present
        url = extract_url(message.content)
        print(f"[on_reaction_add] Extracted URL for Twitter: {url}")

        try:
            print("[on_reaction_add] Preparing to post to Twitter")
            print(f"[on_reaction_add] Content to post: {message.content}")
            print(f"[on_reaction_add] URL to post: {url}")

            # Post to Twitter
            twitter_service.send_tweet(message.content)

            print("[on_reaction_add] Successfully posted to Twitter")
            logger.info("Successfully posted to Twitter")
            await message.add_reaction('✅')

        except Exception as e:
            print(f"[on_reaction_add] Twitter Posting EXCEPTION: {e}")
            print(f"[on_reaction_add] Twitter Posting Traceback: {traceback.format_exc()}")
            logger.error(f"Error posting to Twitter: {e}")
            await message.add_reaction('❌')

def main():
    print("[main] ENTRY: Starting Discord bot...")
    bot.run(DISCORD_TOKEN)
    print("[main] EXIT: Discord bot run completed")

if __name__ == "__main__":
    main()
