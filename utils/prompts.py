from typing import List
import humanize
from datetime import timedelta
class SummaryPrompts:
    @staticmethod
    def get_system_prompt() -> str:
        return """
        You are an assistant tasked with creating high-priority, relevant bullet points from Discord messages, focusing on technical updates, philosophical insights, or notable discussions.
        Each message includes channel and message IDs required to create accurate Discord message links.

        Requirements:
        1. Select an emoji that represents the type of each update (e.g., technical, philosophical, infrastructure).
        2. Include only critical updates or engaging discussions. Avoid minor preferences, general settings, or routine tech support details.
        3. Format each Discord link as follows: https://discord.com/channels/668903786361651200/{channel_id}/{message_id}.
        4. Embed links naturally within sentences, using active verbs and avoiding generic phrases like "[More details]."
        5. For multiple links in a single bullet, ensure they integrate smoothly within a structured sentence.
        6. Capture updates with technical, philosophical, or strategic significance while skipping minor configuration preferences or non-impactful discussions.
        7. Use precise terminology, and avoid making assumptions about user roles (e.g., don’t label someone as "Developer" unless specified).
        8. Distinguish between 'Nodo' by Jossemii and the Ergo Node, and ensure they're not conflated.

        Example:
        Given message with channel_id: 123456 and message_id: 789012
        - 🔧 **Node Update**: kushti [introduced](https://discord.com/channels/668903786361651200/123456/789012) a new block validation process to enhance network security.
        """

    @staticmethod
    def get_user_prompt(chunk: str, current_bullets: int) -> str:
        return f"""
        Create concise, relevant bullet points from the provided Discord messages, using the channel_id and message_id to create Discord links.

        Guidelines:
        - Focus on high-priority updates, including technical, philosophical, or strategically important insights. Exclude routine settings preferences, minor configuration mentions, and basic support issues.
        - Construct Discord links in the format: https://discord.com/channels/668903786361651200/{{channel_id}}/{{message_id}}.
        - Embed links using active verbs, avoiding generic "[More details]" phrases.
        - Select fitting emojis to match each update’s focus, capturing only valuable developments or discussions.
        - Avoid making assumptions about user roles (e.g., "Developer") unless explicitly stated.
        - Remember: 'Nodo' by Jossemii is not the same as the Ergo Node; keep them distinct.

        Current count of valid bullets: {current_bullets}
        Focus on capturing the most relevant, engaging updates.

        Content to analyze (includes channel_id and message_id for link generation):
        {chunk}
        """

    @staticmethod
    def get_final_summary_prompt(bullets: List[str], days_covered: int) -> str:
        return f"""
        Create a comprehensive summary from the provided bullet points, covering the past {days_covered} days.

        Structure:

        ## Updates from the Past {days_covered} Days

        Include all essential information, presenting each update in its most relevant context.

        Requirements:
        1. **Retain every unique detail** without summarizing away key insights or technical information.
        2. **Group related updates** on the same project or topic into one bullet point, consolidating distinct details:
        - Use one entry per project, maintaining all relevant links within it.
        - For instance, if several Satergo updates relate to offline vault features, integrate them.
        3. **Retain Discord links exactly as provided**.
        4. Choose emojis based on the content type (technical, philosophical, infrastructure, etc.).
        5. Prioritize clarity and retain details without making role assumptions.
        6. Avoid separate entries for closely related updates.
        7. Ensure distinction between **Nodo by Jossemii** and **Ergo Node**.
        8. Include an emoji with each bullet point.
        9. Focus on insightful discussions, like technical implementations or strategic philosophies, excluding minor preferences or routine support requests.

        This summary should be concise yet comprehensive, capturing each significant update in one bullet point per project or topic.

        Input bullets:
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
        2. Start with a brief introductory paragraph explaining the post’s scope.
        3. Structure the content into clear sections with bullet points for each detailed update:
        - ## Core Development
            - **Project Name**: Brief summary of the update. [Discussed here](#)
        - ## dApp & Tool Development
            - **Tool Name**: Update details. [Discussed here](#)
        - ## Infrastructure & Integration
            - **Infrastructure Component**: Update details. [Discussed here](#)
        - ## Community & Ecosystem
            - **Community Event**: Summary of the event. [Discussed here](#)

        4. For each update, include:
        - **All unique technical details** without omitting key points.
        - Expand abbreviations and technical terms where helpful.
        - Consolidate related updates on the same topic into a single, clear bullet point.
        - **Bold all project names** and use `[discussed here]` for links.
        - Add context for newer community members.

        5. Writing style:
        - Use accessible, clear language suitable for Reddit while maintaining technical accuracy.
        - Use bullet points for readability and engagement.
        - Provide enough context and background to make updates understandable to a broader audience.
        
        6. Notes:
        - This version should be highly comprehensive, with all technical details included.
        - Do not conflate **Nodo by Jossemii** with the **Ergo Node**.

        Original detailed bullets to expand from:
        {bullets}
        """



    def generate_bullet(self, content: str) -> str:
        """Generate a single bullet point."""
        return f"- {content}"
