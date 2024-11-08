from typing import List
import humanize
from datetime import timedelta

class SummaryPrompts:
    @staticmethod
    def convert_days_to_readable(days_covered: int) -> str:
        """Convert days to a human-readable time period."""
        if days_covered == 1:
            return "day"
        elif days_covered <= 7:
            return "last week"
        else:
            return humanize.naturaldelta(timedelta(days=days_covered))

    @staticmethod
    def _get_common_requirements() -> str:
        """Common requirements shared across prompts."""
        return """
        Core Requirements:
        1. Format Discord links as: https://discord.com/channels/668903786361651200/{channel_id}/{message_id}
        2. Use precise terminology and avoid making assumptions about user roles
        3. Never refer to an "Ergo team" - instead refer to specific software components (e.g., "Reference Client" or "Node")
        4. Distinguish between 'Nodo' by Jossemii and the Ergo Node
        5. Keep project names concise:
           - Use base names without descriptors (e.g., "ErgoPay" not "ErgoPay Implementation")
           - Put version info and context in descriptions
           - Maintain consistent capitalization (e.g., "duckpools" not "Duckpools")
        6. For GroupAnonymousBot messages:
           - Attribute to the relevant project based on context
           - Maintain technical accuracy while being clear about the source
        7. Channel Context:
           - Consider the channel's name and category when interpreting messages
           - Ensure updates reflect the appropriate context of their source channel
           - Frame updates according to the channel's typical subject matter
        """

    @staticmethod
    def get_system_prompt() -> str:
        """Initial processing prompt for converting chunks into updates."""
        return f"""
        You are an advanced summarization assistant creating high-priority, relevant updates from Discord messages.
        Focus on technical updates, philosophical insights, or notable discussions.

        {SummaryPrompts._get_common_requirements()}

        Summarization Imperatives:
        1. Emoji and Update Categorization:
           - Select a PRECISE emoji that captures the CORE essence of the update
           - Prioritize UNIQUE and SIGNIFICANT developments
           - Avoid redundant or marginally different points
           - Consider channel context when selecting categories

        2. Consolidation Principles:
           - STRICTLY merge similar topics into a SINGLE, COMPREHENSIVE bullet
           - Highlight the MOST DISTINCTIVE aspect of each discussion
           - Eliminate EXACT or NEAR-DUPLICATE information
           - Create a narrative that connects individual updates

        3. Linking and Context:
           - Embed links naturally using [text](#) format
           - Provide CONCISE context that bridges technical depth with broader understanding
           - Use consistent, clear linking phrases
           - Consider channel context in framing updates

        4. Filtering Criteria:
           - Include ONLY critical updates or deeply engaging discussions
           - Skip minor configuration preferences
           - Capture updates with strategic or philosophical significance

        Unique Perspective Guidelines:
        - For similar topics, extract THE MOST INNOVATIVE or IMPACTFUL point
        - When multiple sources discuss similar themes, SYNTHESIZE their unique contributions
        - Emphasize the DISTINCTIVE viewpoint of each contributor

        Example:
        From a development channel message:
        🔧 **Node**: kushti [introduced](https://discord.com/channels/668903786361651200/123456/789012) a novel block validation process enhancing network security.
        """

    @staticmethod
    def get_user_prompt(chunk: str, current_bullets: int) -> str:
        """Prompt for processing a specific chunk of messages."""
        return f"""
        Create concise, relevant updates from the provided Discord messages. Each message includes its channel name and category, which provide important context about the discussion's typical subject matter and purpose.

        Current count of valid updates: {current_bullets}
        ADVANCED Consolidation Guidelines:
        - ELIMINATE near-identical points IMMEDIATELY
        - Extract ONLY the most INNOVATIVE or IMPACTFUL element from similar discussions
        - Prioritize updates that offer UNIQUE technical or philosophical insights
        - Maintain PRECISE technical accuracy while AVOIDING REDUNDANCY
        - Consider channel context when crafting updates

        Content Synthesis Strategy:
        1. If multiple messages discuss similar topics:
           - Identify the SINGLE most distinctive contribution
           - Create ONE comprehensive bullet that captures the core insight
        2. Preserve the UNIQUE voice of key contributors
        3. Ensure EACH bullet adds SUBSTANTIVE value to the summary
        4. Format: emoji **Category**: Content with [link](discord_url)

        Content to analyze (includes channel name, category, and message metadata):
        {chunk}
        """

    @staticmethod
    def get_final_summary_prompt(bullets: List[str], days_covered: int) -> str:
        """Prompt for creating a comprehensive final summary."""
        time_period = SummaryPrompts.convert_days_to_readable(days_covered)
        return f"""
        Create a PRECISE, NON-REDUNDANT summary of updates from the past {time_period}.

        {SummaryPrompts._get_common_requirements()}

        ADVANCED Summary Construction:
        1. Thematic Sections (Prioritize UNIQUE Insights):
           ## Core Technical Developments
           ## Regulatory and Market Dynamics
           ## Philosophical Perspectives
           ## Community Interactions

        2. STRICT Consolidation Imperatives:
           - ELIMINATE all redundant or repeated information
           - SYNTHESIZE similar points into a SINGLE, COMPREHENSIVE bullet
           - Highlight the MOST DISTINCTIVE aspect of each discussion
           - Create a CONCISE narrative flow connecting updates

        3. Perspective Preservation:
           - Capture the UNIQUE voice of key contributors
           - Emphasize INNOVATIVE thoughts or breakthrough insights
           - Provide MINIMAL but IMPACTFUL context

        Bullet Point Refinement Rules:
           - MERGE discussions with significant overlap
           - DISTINCTLY characterize different viewpoints
           - Ensure EACH bullet offers UNIQUE, NON-REPETITIVE information

        Original updates to synthesize:
        {bullets}

        Final Output Requirements:
        - Markdown formatted document
        - MAXIMUM information density
        - CLEAR differentiation between topics
        - ENGAGING narrative balancing technical depth and broader context
        """

    @staticmethod
    def get_reddit_summary_prompt(bullets: List[str], days_covered: int) -> str:
        """Prompt for creating detailed Reddit summaries."""
        time_period = SummaryPrompts.convert_days_to_readable(days_covered)

        return f"""
        Create an ENGAGING, COMPREHENSIVE Reddit post summarizing Ergo ecosystem updates from the past {time_period}.

        {SummaryPrompts._get_common_requirements()}

        Structured Summary with DISTINCTIVE Insights:
        1. Title: **# Ergo Ecosystem Deep Dive - {days_covered} Day Roundup**
        2. Compelling introductory paragraph highlighting the MOST SIGNIFICANT developments

        Section Guidelines:
        ## Core Development Breakthroughs
        ## Regulatory Landscape
        ## Market and Philosophical Perspectives
        ## Community Innovation

        Advanced Content Strategies:
        1. CONSOLIDATE related points into SINGULAR, IMPACTFUL bullets
        2. ELIMINATE redundant or marginally different discussions
        3. Preserve UNIQUE contributor perspectives
        4. Balance technical depth with broader ecosystem context

        Narrative Principles:
        - Connect individual updates into a COHESIVE story
        - Highlight INNOVATIVE thoughts and breakthrough insights
        - Provide ACCESSIBLE explanations for technical concepts

        Original updates to synthesize:
        {bullets}

        Final Presentation:
        - Clear, engaging markdown formatting
        - MAXIMUM information density
        - Narrative that EXCITES and INFORMS the Reddit community
        """

    def generate_bullet(self, content: str) -> str:
        """Generate a single bullet point."""
        return f"- {content}"
