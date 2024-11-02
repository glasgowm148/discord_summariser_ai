"""Prompts for generating summaries."""

class SummaryPrompts:
    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt for bullet point generation."""
        return """You are a technical writer for the Ergo blockchain platform. Your task is to create clear, informative bullet points from Discord chat messages. Each bullet point should:

1. Start with a relevant emoji that matches the content and nature of the update
2. Include the project name in bold (**Project Name**)
3. Reference the original message with a Discord link using the exact channel_id and message_id from the message
4. Provide detailed information about the update, including:
   - Specific technical details and changes
   - Impact or implications of the update
   - Any relevant context or dependencies
   - Names of key contributors when mentioned
5. Focus on technical details and development progress
6. Maintain a professional tone

Example format:
- 🔧 **Project Name**: Developer [announced](discord-link) specific technical update. Additional context or details about the update.

IMPORTANT: When creating Discord links, you must use the exact channel_id and message_id from each message's metadata. The link format must be: https://discord.com/channels/668903786361651200/[channel_id]/[message_id]
"""

    @staticmethod
    def get_user_prompt(chunk: str, current_bullets: int) -> str:
        """Get the user prompt for bullet point generation."""
        return f"""Create detailed bullet points from these Discord messages, focusing on development updates and technical information. Current bullet count: {current_bullets}.

Messages:
{chunk}

Requirements:
1. Start each bullet with "- " followed by an appropriate emoji that matches the content
2. Put project names in bold using **Project Name** format
3. Include Discord message links using [text](link) format, where the link MUST use the exact channel_id and message_id from the message metadata in format: https://discord.com/channels/668903786361651200/[channel_id]/[message_id]
4. Focus on technical details and development progress, including:
   - Specific changes or updates made
   - Technical implementation details
   - Impact on users or the ecosystem
   - Dependencies or requirements
   - Names of key contributors
5. Be specific about what was updated or changed
6. Maintain a professional tone
7. Exclude casual conversations or non-development topics
8. IMPORTANT: Use the exact channel_id and message_id from each message's metadata to construct Discord links. Do not make up or modify these IDs.

Key Project Categories to Watch For:
- ErgoHack Projects (OnErgo, 3D Explorer, Minotaur, Miner Rights Protocol, Last Byte Bar, Satergo)
- DeFi/Infrastructure (Rosen Bridge, DuckPools, Gluon, Bober YF, RocksDB, DexYUSD, CyberVerse)
- Documentation (Ergo One Stop Shop)
- Technical Infrastructure (Browser compatibility, permissions)

For each message, look at its metadata (channel_id and message_id) and use those exact values in the Discord link.
"""

    @staticmethod
    def get_final_summary_prompt(bullets: list, days_covered: int) -> str:
        """Get the prompt for final summary generation."""
        bullet_text = "\n".join(bullets)
        return f"""Create a comprehensive development update from these bullet points, covering the past {days_covered} days. Format it as follows:

## Development Updates from the Past {days_covered} Days

[Bullet points with the following format]
- [Appropriate emoji] **Project Name**: Developer [announced](discord-link) specific technical update, including implementation details, dependencies, and impact. Additional context or technical specifications about the update.

Requirements:
1. Keep all bullet points with their emojis, ensuring each emoji is relevant to its update
2. Maintain project names in bold
3. Keep all Discord links exactly as they are - do not modify any channel_ids or message_ids
4. Group related updates for the same project into single bullets
5. Maintain technical accuracy and details, including:
   - Specific changes and implementations
   - Technical requirements and dependencies
   - Impact on users or ecosystem
   - Names of key contributors
6. Keep the format consistent with the example
7. Include all important technical updates
8. IMPORTANT: Do not modify any Discord links - they must keep their original channel_ids and message_ids

Key Categories to Cover:
- ErgoHack Projects and Updates
- DeFi and Infrastructure Development
- Documentation and Resources
- Technical Infrastructure Notes
"""

    @staticmethod
    def get_reddit_summary_prompt(bullets: list, days_covered: int) -> str:
        """Get the prompt for Reddit summary generation."""
        bullet_text = "\n".join(bullets)
        return f"""Create a detailed, Reddit-friendly development update from these bullet points, covering the past {days_covered} days. Format it as follows:

# Ergo Ecosystem Update - {'Weekly' if days_covered > 5 else 'Daily'} Roundup

Hello, Ergo community! In this post, we will cover the latest development updates from the Ergo ecosystem over the past {days_covered} days. This roundup includes insights from core development activities, dApp and tool advancements, infrastructure improvements, and community engagement events. Let's dive in!

## Core Development
[Include core protocol updates, node improvements, and fundamental infrastructure changes]

## dApp & Tool Development
[Include updates about dApps, tools, bridges, and ecosystem applications]

## Community & Ecosystem
[Include community initiatives, governance, and broader ecosystem updates]

Bullet points to expand:
{bullet_text}

Requirements:
1. Organize content into clear sections with detailed explanations
2. Maintain all technical details and keep Discord links exactly as they are - do not modify any channel_ids or message_ids
3. Group related updates together within each section
4. Keep project names in bold
5. Add context and explanations to make technical concepts accessible
6. Use a professional yet engaging tone
7. Include all important technical details with proper context
8. End with a call to action encouraging community engagement
9. IMPORTANT: Do not modify any Discord links - they must keep their original channel_ids and message_ids

Key Categories to Cover:
- ErgoHack Projects (OnErgo, 3D Explorer, Minotaur, etc.)
- DeFi/Infrastructure Updates (Rosen Bridge, DuckPools, etc.)
- Documentation and Resources
- Technical Infrastructure Notes

For each update, include:
- Specific technical details and changes
- Impact or implications of updates
- Dependencies and requirements
- Names of key contributors
- Links to resources when available"""
