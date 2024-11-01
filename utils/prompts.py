from typing import List


class SummaryPrompts:
    @staticmethod
    def get_system_prompt() -> str:
        return """
        You are an assistant tasked with creating detailed, high-priority technical bullet points from Discord messages.
        Each message contains a channel ID and message ID that must be used to create Discord message links.

        Requirements:
        1. Choose an emoji that best represents the content of each update.
        2. Focus on preserving key technical details, including features, code changes, and project specifics.
        3. IMPORTANT: Each Discord link must follow the format: https://discord.com/channels/668903786361651200/{channel_id}/{message_id}
        4. Integrate links smoothly into sentences using active, action-oriented verbs.
        5. For multiple links in a bullet, ensure they flow naturally within a single structured sentence.
        6. Focus exclusively on technical and development updates.
        7. Use clear, accurate technical terminology and prioritize precision.

        Example format:
        Given message with channel_id: 123456 and message_id: 789012
        - 🔧 **Node**: kushti [introduced](https://discord.com/channels/668903786361651200/123456/789012) a new block validation method to enhance security.
        """

    @staticmethod
    def get_user_prompt(chunk: str, current_bullets: int) -> str:
        return f"""
        Create detailed, action-oriented technical bullet points from the provided Discord messages.
        Ensure each bullet uses the channel_id and message_id from the message to create a Discord link.

        Guidelines:
        - Focus on essential technical updates, code changes, and implementation specifics.
        - Construct Discord links using the format: https://discord.com/channels/668903786361651200/{{channel_id}}/{{message_id}}
        - Embed links within sentences using action verbs and avoid standalone "[More details]" references.
        - Select fitting emojis for content type and focus on capturing every major update.

        Current count of valid bullets: {current_bullets}
        Identify additional high-priority technical updates.

        Content to analyze (includes channel_id and message_id for link generation):
        {chunk}
        """

    @staticmethod
    def get_final_summary_prompt(bullets: List[str], days_covered: int) -> str:
        return f"""
        Create a detailed, structured technical summary from the provided bullet points covering {days_covered} days.

        Use this outline:
        
        ## Development Updates from the Past {days_covered} Days
        
        Retain ALL technical updates, structured as follows:
        - Node and Protocol Changes
        - Infrastructure Improvements
        - dApp Development
        - Tools and Services
        - Technical Integrations
        - Security Updates
        - Additional Development-Related Content
        - Insightful/Philosophical Community Discussions
        
        Requirements:
        1. Maintain ALL technical details without summarizing away essential information.
        2. Group related updates by consolidating multiple updates about the same project into single, comprehensive bullet points:
           - Combine related information from the same project/topic into one detailed entry
           - Include all relevant links within the consolidated entry
           - Ensure the combined entry captures all unique technical details without redundancy
           - Example: Multiple Satergo updates about the same feature should be combined into one detailed bullet point
        3. Keep Discord links precisely as they appear in the input.
        4. Choose suitable emojis based on the update type.
        5. Prioritize clarity and accuracy for each technical detail.
        6. Avoid creating separate entries for updates that are part of the same development effort.
        
        Input bullets:
        {bullets}
        """

    @staticmethod
    def get_reddit_summary_prompt(bullets: List[str], days_covered: int) -> str:
        return f"""
        Create a comprehensive Reddit post summarizing development updates from the Ergo ecosystem over the past {days_covered} days.
        Use the original, detailed bullet points to create an informative and engaging post.

        Key Requirements:
        1. Begin with a title using this format:
           # Ergo Development Update - {days_covered} Day Roundup
        2. Start with a brief introduction paragraph explaining what this update covers.
        3. Structure the content into clear sections:
           ## Core Development
           ## dApp & Tool Development
           ## Infrastructure & Integration
           ## Community & Ecosystem
        4. For each update:
           - Include all technical details from the original bullets
           - Expand abbreviations and explain technical terms where helpful
           - Group related updates together into coherent paragraphs
           - Keep all project names in **bold**
           - Convert Discord links into `[discussed here]` inline links
        5. Writing style:
           - Use clear, engaging language suitable for Reddit
           - Maintain technical accuracy while being accessible
           - Add context where helpful for newer community members
           - Use proper markdown formatting for readability
        6. Unlike the Discord summary, this version should:
           - Be more detailed and comprehensive
           - Include more context and explanations
           - Use full paragraphs where appropriate
           - Maintain all technical information from original bullets

        Original detailed bullets to expand from:
        {bullets}
        """
