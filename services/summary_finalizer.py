"""Service for finalizing and formatting summaries for different platforms."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from openai import OpenAI

from config.settings import OUTPUT_DIR
from services.base_service import BaseService
from services.project_manager import ProjectManager
from utils.prompts import SummaryPrompts
from helpers.processors.text_processor import TextProcessor
from helpers.formatters.content_formatter import ContentFormatter
from helpers.formatters.social_media_formatter import SocialMediaFormatter
from helpers.validators.content_validator import ContentValidator


class SummaryFinalizer(BaseService):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.project_manager = ProjectManager()
        self.initialize()

    def initialize(self) -> None:
        """Initialize OpenAI client."""
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            self.handle_error(e, {"context": "OpenAI client initialization"})
            raise

    def create_final_summary(
        self, updates: List[str], days_covered: int, hackmd_url: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Create summaries for different platforms."""
        try:
            # Store original updates for Reddit version
            original_updates = updates.copy()

            # Validate categories and clean up formatting
            validated_updates = ContentValidator.validate_categories(updates)
            
            # Remove duplicates
            unique_updates = ContentValidator.remove_duplicate_updates(validated_updates)
            
            # Create Discord summary (condensed version)
            discord_summary, discord_summary_with_cta = self._create_discord_summary(
                unique_updates, days_covered, hackmd_url
            )

            # Create Reddit summary (detailed version)
            reddit_summary = self._create_reddit_summary(original_updates, days_covered)

            # Learn from the summaries
            if discord_summary:
                self.project_manager.learn_from_summary(discord_summary)
            if reddit_summary:
                self.project_manager.learn_from_summary(reddit_summary)

            # Save summaries
            self._save_summaries(discord_summary, discord_summary_with_cta, reddit_summary)

            return discord_summary, discord_summary_with_cta, reddit_summary

        except Exception as e:
            self.handle_error(e, {"context": "Creating summaries"})
            return None, None, None

    def _create_discord_summary(
        self, unique_updates: List[str], days_covered: int, hackmd_url: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Create the condensed Discord summary."""
        try:
            # Create section header
            header = ContentFormatter.format_header(f"Updates from the Past {days_covered} Days")
            
            # Format the summary
            final_summary = ContentFormatter.format_discord_summary(header, unique_updates)
            
            # Clean up formatting
            final_summary = ContentFormatter.clean_formatting(final_summary)
            
            # Add HackMD link if available
            if hackmd_url:
                final_summary += f"\n\n[Full Summary on HackMD]({hackmd_url})"
            
            # Create version with call to action
            summary_with_cta = ContentFormatter.add_call_to_action(final_summary)
            
            return final_summary, summary_with_cta
            
        except Exception as e:
            self.handle_error(e, {"context": "Creating Discord summary"})
            return None, None

    def _create_reddit_summary(
        self, original_updates: List[str], days_covered: int
    ) -> Optional[str]:
        """Create a detailed Reddit summary."""
        try:
            # Get project context and create prompt
            project_contexts = self.project_manager.get_all_project_contexts()
            prompt = self._create_reddit_prompt(project_contexts, original_updates, days_covered)

            # Generate content using OpenAI
            reddit_content = self._generate_reddit_content(prompt)
            if not reddit_content:
                self.logger.error("Failed to generate Reddit content")
                return None

            # Pre-process content to ensure it has valid structure
            if not any(line.strip().startswith('#') for line in reddit_content.split('\n')):
                reddit_content = f"# Ergo Updates\n\n{reddit_content}"

            # Validate and clean the content
            cleaned_content, is_valid = ContentValidator.validate_and_clean_summary(reddit_content)
            if not is_valid:
                self.logger.error("Reddit content validation failed")
                return None
                
            # Format and clean
            cleaned_content = ContentFormatter.clean_formatting(cleaned_content)
                
            # Add footer
            footer = (
                "*This summary is generated from the Ergo Discord. "
                "Join us on [Discord](https://discord.gg/ergo-platform-668903786361651200) for real-time updates "
                "and discussions!*"
            )
            final_content = f"{cleaned_content}\n\n---\n\n{footer}"
            
            return final_content
            
        except Exception as e:
            self.handle_error(e, {"context": "Creating Reddit summary"})
            return None

    def _create_reddit_prompt(self, project_contexts: str, updates: List[str], days_covered: int) -> str:
        """Create the prompt for Reddit summary generation."""
        return f"""Previous project context:
{project_contexts}

{SummaryPrompts.get_reddit_summary_prompt(updates, days_covered)}"""

    def _generate_reddit_content(self, prompt: str) -> Optional[str]:
        """Generate Reddit content using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical writer for the Ergo blockchain platform. "
                                  "Your task is to create a detailed Reddit summary. "
                                  "Focus on technical achievements and positive developments. "
                                  "IMPORTANT: When including Discord links, use the exact channel_id "
                                  "and message_id from the original updates - do not modify these IDs.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.7,
                max_tokens=4000,
            )

            content = response.choices[0].message.content
            return content.strip() if content else None
            
        except Exception as e:
            self.handle_error(e, {"context": "Generating Reddit content"})
            return None

    def format_for_social_media(self, content: str, platform: str) -> str:
        """Format content for a specific social media platform."""
        try:
            return SocialMediaFormatter.format_for_platform(content, platform)
        except Exception as e:
            self.handle_error(e, {"context": f"Formatting for {platform}"})
            return content

    def _save_summaries(
        self,
        discord_summary: Optional[str],
        discord_summary_with_cta: Optional[str],
        reddit_summary: Optional[str]
    ) -> None:
        """Save all summaries to file."""
        try:
            if discord_summary:
                self._save_to_sent_summaries("Discord", discord_summary)
            if discord_summary_with_cta:
                self._save_to_sent_summaries("Discord with CTA", discord_summary_with_cta)
            if reddit_summary:
                self._save_to_sent_summaries("Reddit", reddit_summary)
        except Exception as e:
            self.handle_error(e, {"context": "Saving summaries"})

    def _save_to_sent_summaries(self, format_type: str, content: str) -> None:
        """Save formatted summary to output/sent_summaries.md."""
        try:
            # Ensure output directory exists
            output_dir = Path(OUTPUT_DIR)
            output_dir.mkdir(exist_ok=True)

            # Create summary header with current date
            current_date = datetime.now().strftime("%Y-%m-%d")
            header = ContentFormatter.format_header(f"{format_type} Summary {current_date}")
            formatted_content = f"\n{header}\n\n{content}\n"

            # Append to sent_summaries.md
            summaries_file = output_dir / "sent_summaries.md"
            with open(summaries_file, "a") as f:
                f.write(formatted_content)

            self.logger.info(f"Saved {format_type} summary to output/sent_summaries.md")
        except Exception as e:
            self.handle_error(e, {"context": f"Saving {format_type} summary"})
