from typing import List
import humanize
from datetime import timedelta
class SummaryPrompts:
    @staticmethod
    def get_system_prompt() -> str:
        return """
        You are an assistant tasked with creating high-priority, relevant updates from Discord messages, focusing on technical updates, philosophical insights, or notable discussions.
        Each message includes channel and message IDs required to create accurate Discord message links.

        Requirements:
        1. Select an emoji that represents the type of each update (e.g., technical, philosophical, infrastructure).
        2. Include only critical updates or engaging discussions. Avoid minor preferences, general settings, or routine tech support details.
        3. Format each Discord link as follows: https://discord.com/channels/668903786361651200/{channel_id}/{message_id}.
        4. Embed links naturally within sentences using [text](#) format, using active verbs and avoiding generic phrases.
        5. For multiple links in a single topic, integrate them smoothly within a natural paragraph.
        6. Capture updates with technical, philosophical, or strategic significance while skipping minor configuration preferences or non-impactful discussions.
        7. Use precise terminology, and avoid making assumptions about user roles (e.g., don't label someone as "Developer" unless specified).
        8. Distinguish between 'Nodo' by Jossemii and the Ergo Node, and ensure they're not conflated.
        9. When handling messages from GroupAnonymousBot:
           - These are bridged messages from project channels
           - Attribute to the project/team rather than "GroupAnonymousBot"
           - Use the channel context to determine the correct project attribution
           - Example: "The Rosen team announced..." instead of "GroupAnonymousBot shared..."
        10. Always provide full context for technical discussions:
           - Include relevant background information
           - Explain the significance of updates
           - Connect related points across messages
           - Maintain technical accuracy while being clear
        11. Keep project names concise and simple:
           - Use the base project name without additional descriptors
           - Examples:
             * "ErgoPay" (not "Ergopay Implementation" or "ErgoPay Updates")
             * "Rosen" (not "Rosen Liquidity Remarks" or "Rosen Bridge Update")
             * "duckpools" (not "Duckpools v2 Improvements" or "Duckpools Protocol")
           - Only include version numbers or additional context in the description, not the project name

        Example:
        Given message with channel_id: 123456 and message_id: 789012
        🔧 **Node**: kushti [introduced](https://discord.com/channels/668903786361651200/123456/789012) a new block validation process to enhance network security.
        """

    @staticmethod
    def get_user_prompt(chunk: str, current_bullets: int) -> str:
        return f"""
        Create concise, relevant updates from the provided Discord messages, using the channel_id and message_id to create Discord links.

        Guidelines:
        - Focus on high-priority updates, including technical, philosophical, or strategically important insights. Exclude routine settings preferences, minor configuration mentions, and basic support issues.
        - Construct Discord links in the format: [text](https://discord.com/channels/668903786361651200/{{channel_id}}/{{message_id}}).
        - Embed links naturally within sentences, avoiding generic phrases.
        - Select fitting emojis to match each update's focus, capturing only valuable developments or discussions.
        - Avoid making assumptions about user roles (e.g., "Developer") unless explicitly stated.
        - Remember: 'Nodo' by Jossemii is not the same as the Ergo Node; keep them distinct.
        - For GroupAnonymousBot messages:
          * Attribute to the relevant project/team based on the channel
          * Provide full context of the project's update or announcement
          * Maintain the original technical details while making the source clear
          * Example: "The Rosen team announced..." instead of "GroupAnonymousBot shared..."
        - Keep project names concise:
          * Use base names without descriptors (e.g., "ErgoPay" not "ErgoPay Implementation")
          * Put version info and context in the description, not the project name
          * Maintain consistent capitalization (e.g., "duckpools" not "Duckpools")

        Current count of valid updates: {current_bullets}
        Focus on capturing the most relevant, engaging updates.

        Content to analyze (includes channel_id and message_id for link generation):
        {chunk}
        """

    @staticmethod
    def get_final_summary_prompt(bullets: List[str], days_covered: int) -> str:
        return f"""
        Create a comprehensive summary from the provided updates, covering the past {days_covered} days.

        Structure:

        ## Updates from the Past {days_covered} Days

        Requirements:
        1. **Format each update as a bullet point**:
           - Start each update with "- " followed by an emoji and project name in bold
           - Example: "- 🔧 **Project**: Description with [links](#)"
        2. **Merge related updates** into single bullet points:
           - Combine multiple points about the same topic/project into one comprehensive bullet
           - Integrate all Discord links naturally within the text using [text](#) format
           - Ensure the merged bullet provides a complete picture of the topic
        3. **Retain every unique detail** without summarizing away key insights or technical information.
        4. Choose emojis based on the content type (technical, philosophical, infrastructure, etc.).
        5. Prioritize clarity and retain details without making role assumptions.
        6. Ensure distinction between **Nodo by Jossemii** and **Ergo Node**.
        7. Focus on insightful discussions, like technical implementations or strategic philosophies, excluding minor preferences or routine support requests.
        8. For project updates (especially from GroupAnonymousBot):
            - Attribute to the project/team rather than the bot
            - Provide complete context of the update
            - Maintain technical accuracy while being clear about the source
            - Example: "The Rosen team announced..." instead of "GroupAnonymousBot shared..."
        9. Keep project names concise and consistent:
            - Use base project names without descriptors
            - Include version numbers and context in descriptions
            - Examples:
              * "**ErgoPay**" not "**ErgoPay Implementation**"
              * "**Rosen**" not "**Rosen Liquidity Remarks**"
              * "**duckpools**" not "**Duckpools v2**"

        This summary should present each topic as a single, comprehensive bullet point that captures all related information.

        Input updates:
        {bullets}
        """

    @staticmethod
    def get_reddit_summary_prompt(bullets: List[str], days_covered: int) -> str:
        # Convert days_covered to a human-readable format
        if days_covered == 1:
            time_period = "day"
        elif days_covered <= 7:
            time_period = "last week"
        else:
            time_period = humanize.naturaldelta(timedelta(days=days_covered))
        return f"""
        Create an engaging, fully comprehensive Reddit post summarizing development updates from the Ergo ecosystem over the past {time_period}. 

        Requirements:
        1. Begin with a title in this format:
        **# Ergo Development Update - {days_covered} Day Roundup**
        2. Start with a brief introductory paragraph explaining the post's scope.
        3. Structure the content into clear sections with bullet points for each project:
        - ## Core Development
            - **Project**: Comprehensive update merging all related points into a flowing narrative. Include all links naturally as [discussed here](#).
        - ## dApp & Tool Development
            - **Tool**: Detailed update integrating all points about the tool into a cohesive story.
        - ## Infrastructure & Integration
            - **Component**: Thorough update combining all related information into a clear narrative.
        - ## Community & Ecosystem
            - **Event**: Complete summary merging all event details into an engaging story.

        4. For each update:
        - **Merge all related points** into a comprehensive bullet point
        - **Include all unique technical details** without omitting key points
        - Expand abbreviations and technical terms where helpful
        - **Bold project names** (keeping them concise) and integrate links naturally
        - Add context for newer community members

        5. Writing style:
        - Use accessible, clear language suitable for Reddit while maintaining technical accuracy
        - Create flowing narratives that naturally incorporate all points and links
        - Provide enough context and background to make updates understandable to a broader audience
        
        6. Notes:
        - This version should be highly comprehensive, with all technical details included
        - Do not conflate **Nodo by Jossemii** with the **Ergo Node**
        - For project updates (from GroupAnonymousBot or other sources):
          * Attribute to the project/team rather than the messenger
          * Provide complete context and significance
          * Maintain technical accuracy while being clear about the source
          * Example: "The Rosen team announced..." instead of "GroupAnonymousBot shared..."
        - Keep project names concise:
          * Use base names (e.g., "**ErgoPay**" not "**ErgoPay Implementation**")
          * Put version info in descriptions
          * Maintain consistent capitalization

        Original detailed updates to merge into bullet points:
        {bullets}
        """

    def generate_bullet(self, content: str) -> str:
        """Generate a single bullet point."""
        return f"- {content}"
