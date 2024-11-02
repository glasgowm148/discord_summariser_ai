from typing import List
import humanize
from datetime import timedelta

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
        8. Note: 'Nodo' by Jossemii is not the same as the Ergo Node. Ensure they are not conflated in the summaries.

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
        - Remember: 'Nodo' by Jossemii is distinct from the Ergo Node. Do not conflate them.

        Current count of valid bullets: {current_bullets}
        Identify additional high-priority technical updates.

        Content to analyze (includes channel_id and message_id for link generation):
        {chunk}
        """

    @staticmethod
    def get_final_summary_prompt(bullets: List[str], days_covered: int) -> str:
        return f"""
        Create a comprehensive summary from the provided bullet points, covering the past {days_covered} days.

        Follow this outline exactly:

        ## Updates from the Past {days_covered} Days

        **Retain all significant information** and structure updates to make them as relevant as possible**:


        Requirements:
        1. **Include every unique detail**—do not summarize away critical information.
        2. **Group and consolidate** multiple updates about the same project/topic into a single, comprehensive bullet point:
        - Keep all project details in one combined entry where possible.
        - Include every relevant link within the consolidated entry.
        - Capture every unique aspect while avoiding redundancy.
        - Example: If multiple Satergo updates relate to a single feature, integrate them into one detailed, cohesive bullet point.
        3. **Preserve Discord links precisely as in the input**.
        4. Choose suitable emojis based on the update type (development, infrastructure, community, etc.).
        5. Prioritize clarity and accuracy for every detail.
        6. Do not create separate entries for updates within the same effort.
        7. Important: Be careful not to conflate **Nodo by Jossemii** with the **Ergo Node**; these are distinct.
        8. Important: Remember to include an emoji in each bullet point.
        9. Highlight insightful discussions, excluding price discussions and support requests.

        Important: This is for Discord, so please try and be concise, but do not lose any information. One bullet point per project with an emoji.

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
