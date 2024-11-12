# Community Content Bridge: Discord to Reddit Submission Bot

## Overview
An intelligent AI-powered bot that transforms Discord discussions into engaging Reddit content

## Key Features
- 🌐 Emoji-Triggered Submission
- 🤖 AI-Powered Content Transformation
- 📝 Intelligent Submission Preparation
- 🔍 Context-Aware Processing

## Submission Workflow
1. Add 🌐 emoji to a message
2. Bot analyzes content type
   - URL-based submissions
   - Text-based discussions
3. Generates community-focused title
4. Transforms content for Reddit
5. Sends preview to #bridge-tester

## Submission Types
### Link Submissions
- Extracts URL
- Generates contextual title
- Preserves original link
- Removes personal language

### Text Discussions
- Transforms text for Reddit
- Generates engaging title
- Maintains community voice

## AI Transformation Capabilities
- Removes first-person language
- Adapts content to Reddit's style
- Generates click-worthy titles
- Contextual content processing

## Prerequisites
- Python 3.8+
- Discord bot token
- OpenAI API key
- Libraries:
  - discord.py
  - openai
  - python-dotenv

## Installation
1. Clone repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration (.env)
```
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
DISCORD_WEBHOOK_URL_TESTER=your_webhook_url
```

## Running the Bot
```bash
python services/social_media/reddit_comment_bot.py
```

## Logging & Debugging
- Comprehensive logging in `discord_bot.log`
- Tracks submission process
- Captures AI transformation details

## Customization
- Modify AI prompts
- Adjust transformation logic
- Configure webhook settings

## Troubleshooting
- Check `discord_bot.log`
- Verify API credentials
- Ensure proper bot permissions

## Security & Compliance
- Protects API credentials
- Maintains community standards
- Avoids personal identifiable information

## Limitations
- Depends on OpenAI API
- Content quality varies
- No direct Reddit API posting

## Future Roadmap
- Direct Reddit API integration
- Multi-platform support
- Advanced content filtering
- Customizable transformation rules

## Community Guidelines
- Use 🌐 emoji responsibly
- Respect content origins
- Maintain community spirit

## License
[Specify your license]
