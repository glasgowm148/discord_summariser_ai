"""Prompts for generating structured summaries with unique emojis and linked discussions for Ergo development updates."""

class SummaryPrompts:
    @staticmethod
    def get_system_prompt() -> str:
        """Generate the system prompt for concise, bullet-pointed summaries from Ergo Discord discussions."""
        return """
# Instruction for Ergo Discord Summary Generation

Your task is to distill Discord messages into concise, informative bullet points specifically for the Ergo blockchain platform. Each bullet point should:

- Start with a unique, relevant emoji.
- Bold the project name like this: **Project Name**.
- Include a direct link to the original message, using the message's exact `channel_id` and `message_id` without modification.
- Highlight critical information about the update, such as:
    - Technical changes, new features, or issues
    - Implications for the ecosystem or user experience
    - Dependencies, connections with other projects, or requirements
    - Key contributor names when available

### Example Bullet Format:
- 🛠️ **Satergo**: [Aberg](https://discord.com/channels/668903786361651200/[channel_id]/[message_id]) confirmed initial support for one wallet, with scalable code for future multi-wallet capabilities.

### Key Points to Follow:
1. Use unique emojis per bullet to enhance readability.
2. Embed the original `channel_id` and `message_id` in each link without alteration.
3. Maintain a technical, professional tone that emphasizes development progress.
4. Focus only on relevant, technical messages and skip casual or non-development-related discussions.

### Discord Link Format:
https://discord.com/channels/668903786361651200/[channel_id]/[message_id]
"""

    @staticmethod
    def get_user_prompt(chunk: str, current_bullets: int) -> str:
        """Generate the user prompt to summarize a batch of messages into bullet points."""
        return f"""
# User Instruction for Generating Bullet Points

Condense these Discord messages into bullet points focused on Ergo development. Current bullet count: {current_bullets}.

### Messages:
{chunk}

### Bullet Point Requirements:
1. Begin each bullet with "- " and a unique emoji that fits the content.
2. Bold project names with **Project Name** format.
3. Add a direct link to the original message, ensuring the exact `channel_id` and `message_id` are in the URL: https://discord.com/channels/668903786361651200/[channel_id]/[message_id].
4. Focus on development and technical specifics:
   - Specific changes or updates made
   - Technical details and their impact on the ecosystem
   - Dependencies or contributors’ names
5. Exclude casual conversations and non-technical topics.
6. Use unique emojis for each bullet to differentiate updates clearly.

### Key Project Categories:
- ErgoHack Projects (e.g., OnErgo, 3D Explorer, Minotaur)
- DeFi/Infrastructure (e.g., Rosen Bridge, DuckPools)
- Documentation (e.g., Ergo One Stop Shop)
- Technical Infrastructure (e.g., Browser compatibility, RocksDB)
"""

    @staticmethod
    def get_final_summary_prompt(bullets: list, days_covered: int) -> str:
        """Generate the prompt for compiling a final summary from bullet points."""
        bullet_text = "\n".join(bullets)
        return f"""
# Final Development Summary for Ergo Platform

{bullet_text}
"""

    @staticmethod
    def get_reddit_summary_prompt(bullets: list, days_covered: int) -> str:
        """Generate a Reddit-friendly prompt for an Ergo development update post."""
        bullet_text = "\n".join(bullets)
        return f"""
# Ergo Ecosystem Update for Reddit - {'Weekly' if days_covered > 5 else 'Daily'} Roundup

{bullet_text}
"""
