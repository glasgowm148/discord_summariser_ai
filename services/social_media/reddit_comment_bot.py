import os
import sys
import re
import logging
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv
import requests
import asyncio

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Import RedditService using relative import
from services.social_media.reddit_service import RedditService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordAIBot')

# Load environment variables
load_dotenv('/Users/m/Documents/GitHub/discord_summariser_ai/config/.env')

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

# Initialize RedditService
reddit_service = RedditService()

def extract_url(text):
    """Extract first URL from text"""
    url_pattern = r'https?://\S+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

def generate_reddit_title(content, url=None):
    """Generate a community-focused, engaging Reddit title"""
    try:
        # If URL is about documentation or technical content, use a specific prompt
        if url and ('docs' in url or 'documentation' in content.lower()):
            prompt = f"Create a concise, community-engaging title for a technical documentation link. Avoid first-person language. Content context: {content}"
        else:
            prompt = f"Create a catchy, community-focused title that encourages engagement. Avoid first-person language. Content context: {content}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate a title that sounds like a community post, avoiding personal pronouns."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        title = response.choices[0].message.content.strip()
        
        # Remove surrounding quotes if present
        title = title.strip('"\'')
        
        logger.info(f"Generated Reddit title: {title}")
        return title
    except Exception as e:
        logger.error(f"Error generating Reddit title: {e}")
        # Fallback title generation
        return f"Community Insight: {content[:50]}..." if not url else f"New Resource: {url.split('/')[-1]}"

def prepare_reddit_submission(message_content, url=None):
    """Prepare content for Reddit submission"""
    try:
        # If URL is present, we want a link post
        if url:
            # For documentation or technical links, generate a context-aware title
            title = generate_reddit_title(message_content, url)
            return {
                'title': title,
                'url': url,
                'selftext': ''  # No additional text for link posts
            }
        
        # For text-based posts
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Transform the text into a community-friendly Reddit post. Remove first-person language, make it sound like a community discussion."},
                {"role": "user", "content": message_content}
            ],
            max_tokens=300
        )
        
        transformed_text = response.choices[0].message.content.strip()
        title = generate_reddit_title(message_content)
        
        return {
            'title': title,
            'selftext': transformed_text
        }
    
    except Exception as e:
        logger.error(f"Error preparing Reddit submission: {e}")
        return {
            'title': 'Community Discussion',
            'selftext': message_content
        }

@bot.event
async def on_reaction_add(reaction, user):
    """Handle specific emoji reactions"""
    if user.bot:  # Ignore bot's own reactions
        return

    message = reaction.message
    logger.info(f"Reaction added: {reaction.emoji} by {user.name}")

    # Check for thumbs up emoji (👍) which triggers Reddit submission process
    if str(reaction.emoji) == '👍':
        # Extract URL if present
        url = extract_url(message.content)
        
        # Prepare Reddit submission
        reddit_submission = prepare_reddit_submission(message.content, url)
        
        # Post to Reddit
        try:
            success = await reddit_service.post_to_reddit(
                title=reddit_submission['title'], 
                content=reddit_submission.get('selftext', '') or reddit_submission.get('url', '')
            )
            
            if success:
                logger.info("Successfully posted to Reddit")
                # Optional: Send confirmation to the webhook channel
                await send_to_webhook(f"✅ Reddit Post Successful:\n{reddit_submission['title']}")
            else:
                logger.error("Failed to post to Reddit")
                await send_to_webhook(f"❌ Reddit Post Failed:\n{reddit_submission['title']}")
        
        except Exception as e:
            logger.error(f"Error posting to Reddit: {e}")
            await send_to_webhook(f"❌ Reddit Post Error:\n{e}")

async def send_to_webhook(message):
    """Send message to Discord channel and add reactions"""
    try:
        # Get the channel by ID
        channel = bot.get_channel(954383538474614895)
        
        if channel:
            # Send the message
            sent_message = await channel.send(message)
            
            logger.info("Message sent to channel successfully")
        else:
            logger.error(f"Could not find channel with ID {WEBHOOK_CHANNEL_ID}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

def main():
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
