"""Finalize and format summaries for different platforms."""
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from openai import OpenAI

from utils.prompts import SummaryPrompts
from services.base_service import BaseService
from services.project_manager import ProjectManager
from config.settings import OUTPUT_DIR


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
        self, bullets: List[str], days_covered: int
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Create both Discord and Reddit summaries."""
        try:
            # Store original bullets for Reddit version
            original_bullets = bullets.copy()

            # Create Discord summary (condensed version)
            unique_bullets = self._remove_duplicate_bullets(bullets)
            discord_summary, discord_summary_with_cta = self._create_discord_summary(
                unique_bullets, days_covered
            )

            print(f"Discord Summary: {discord_summary}")
            print(f"Discord Summary with CTA: {discord_summary_with_cta}")

            # Create Reddit summary (detailed version)
            reddit_summary = self._create_reddit_summary(original_bullets, days_covered)

            # Learn from the summaries
            if discord_summary:
                self.project_manager.learn_from_summary(discord_summary)
            if reddit_summary:
                self.project_manager.learn_from_summary(reddit_summary)

            # Save summaries to output/sent_summaries.md
            if discord_summary:
                self._save_to_sent_summaries("Discord", discord_summary)
            if discord_summary_with_cta:
                self._save_to_sent_summaries("Discord with CTA", discord_summary_with_cta)
            if reddit_summary:
                self._save_to_sent_summaries("Reddit", reddit_summary)

            return discord_summary, discord_summary_with_cta, reddit_summary

        except Exception as e:
            self.handle_error(e, {"context": "Creating summaries"})
            return None, None, None

    def _create_discord_summary(
        self, unique_bullets: List[str], days_covered: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """Create the condensed Discord summary."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                project_contexts = self.project_manager.get_all_project_contexts()
                prompt = f"""Previous project context:
{project_contexts}

{SummaryPrompts.get_final_summary_prompt(unique_bullets, days_covered)}"""

                final_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a technical writer for the Ergo blockchain platform. Your task is to create a concise Discord summary. IMPORTANT: When including Discord links, use the exact channel_id and message_id from the original bullet points - do not modify these IDs."
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    temperature=0.6,
                    max_tokens=2000,
                )

                summary_content = final_response.choices[0].message.content

                if not any(line.strip().startswith("-") for line in summary_content.split("\n")):
                    raise ValueError("Generated summary contains no bullet points")

                final_summary = self._clean_final_summary(summary_content)
                summary_with_cta = self._add_call_to_action(final_summary)
                return final_summary, summary_with_cta
            except Exception as e:
                self.logger.warning(f"Discord summary attempt {attempt + 1}/{max_attempts} failed: {str(e)}")
                if attempt == max_attempts - 1:
                    raise

    def _create_reddit_summary(
        self, original_bullets: List[str], days_covered: int
    ) -> Optional[str]:
        """Create a detailed Reddit summary from original bullets."""
        try:
            project_contexts = self.project_manager.get_all_project_contexts()
            prompt = f"""Previous project context:
{project_contexts}

{SummaryPrompts.get_reddit_summary_prompt(original_bullets, days_covered)}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical writer for the Ergo blockchain platform. Your task is to create a detailed Reddit summary. IMPORTANT: When including Discord links, use the exact channel_id and message_id from the original bullet points - do not modify these IDs."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.7,
                max_tokens=4000,
            )

            reddit_content = response.choices[0].message.content
            if not any(line.strip().startswith("#") for line in reddit_content.split("\n")):
                raise ValueError("Generated Reddit content contains no headers")
            cleaned_content = self._clean_reddit_content(reddit_content)
            return cleaned_content
        except Exception as e:
            self.handle_error(e, {"context": "Creating Reddit summary"})
            return None

    def _clean_reddit_content(self, content: str) -> str:
        """Clean and format the Reddit content."""
        # Remove any excess whitespace while preserving markdown formatting
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                if line.startswith("#"):
                    # Ensure proper spacing around headers
                    cleaned_lines.extend(["", line, ""])
                elif line.startswith("-"):
                    # Ensure linebreak before bullet points
                    if not cleaned_lines or not cleaned_lines[-1].strip() == "":
                        cleaned_lines.append("")
                    cleaned_lines.append(line)
                else:
                    cleaned_lines.append(line)

        # Join lines and add Reddit footer
        cleaned_content = "\n".join(cleaned_lines).strip()
        footer = (
            "\n\n---\n*This summary is generated from the Ergo Discord. "
            "Join us on [Discord](https://discord.gg/ergo-platform-668903786361651200) for real-time updates "
            "and discussions!*"
        )
        return cleaned_content + footer

    def format_for_twitter(self, summary: str) -> str:
        """Format the summary to be Twitter-friendly by removing all URLs and formatting."""
        try:
            formatted_lines = []
            for line in summary.split("\n"):
                if not line.strip():
                    continue

                # Remove section headers formatting
                if line.startswith("#"):
                    line = line.lstrip("#").strip()
                    formatted_lines.append(line)
                    continue

                # Process bullet points
                if line.startswith("-"):
                    # Remove bold formatting but keep project names
                    line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)

                    # Remove all URLs including Discord ones
                    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
                    line = re.sub(r"\(https://discord\.com/channels/[^)]+\)", "", line)

                    # Clean up any double spaces and add the line
                    formatted_lines.append(re.sub(r"\s+", " ", line).strip())
                else:
                    # Keep other content (if any) as is
                    formatted_lines.append(line)

            formatted_summary = "\n".join(formatted_lines).strip()

            # Remove the Discord invite link if present
            formatted_summary = re.sub(
                r"\nJoin the discussion on Discord: https://discord\.gg/[^\s]+",
                "",
                formatted_summary,
            )

            return formatted_summary

        except Exception as e:
            self.handle_error(e, {"context": "Formatting for Twitter"})
            return summary

    def _remove_duplicate_bullets(self, bullets: List[str]) -> List[str]:
        """Remove duplicate bullets while preserving the most detailed version."""
        seen_content = {}

        for bullet in bullets:
            # Extract core content without emoji and formatting
            core_content = re.sub(r"🔧|🚀|📊|🔗|🔐|🌐|📦|🔄|🔒", "", bullet)
            core_content = re.sub(r"\[.*?\]\(.*?\)", "", core_content)
            core_content = re.sub(r"\*\*.*?\*\*", "", core_content)
            core_content = core_content.lower().strip()

            # If we haven't seen this content, or this version is more detailed
            if core_content not in seen_content or len(bullet) > len(
                seen_content[core_content]
            ):
                seen_content[core_content] = bullet

        return list(seen_content.values())

    def _clean_final_summary(self, summary: str) -> str:
        """Clean and validate the final summary."""
        # Remove any notes or comments
        summary = re.sub(r"\(Note:.*?\)", "", summary, flags=re.DOTALL)
        summary = re.sub(r"\n\s*\n", "\n", summary)

        # Process each line
        valid_sections = []
        for line in summary.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("#") or line.startswith("-"):
                # Ensure Discord links are preserved exactly
                if "https://discord.com/channels/" in line:
                    # Extract and validate Discord link
                    match = re.search(r'https://discord\.com/channels/\d+/\d+/\d+', line)
                    if match:
                        # Keep the link exactly as is
                        valid_sections.append(line)
                    else:
                        # If link format is invalid, try to fix it
                        line = re.sub(r'https://discord\.com/channels/[^)\s]+', 
                                    'https://discord.com/channels/668903786361651200', line)
                        valid_sections.append(line)
                else:
                    valid_sections.append(line)
            else:
                # For non-header, non-bullet lines, check if they're part of the content
                if len(line) > 10:  # Arbitrary minimum length for content
                    valid_sections.append(line)

        cleaned_summary = "\n".join(valid_sections)

        # Validate the cleaned summary has content
        if not cleaned_summary.strip():
            raise ValueError("Cleaning resulted in empty summary")

        return cleaned_summary

    def _save_to_sent_summaries(self, format_type: str, content: str) -> None:
        """Save formatted summary to output/sent_summaries.md."""
        try:
            # Ensure output directory exists
            output_dir = Path(OUTPUT_DIR)
            output_dir.mkdir(exist_ok=True)
            
            summaries_file = output_dir / 'sent_summaries.md'
            current_date = datetime.now().strftime("%Y-%m-%d")
            formatted_content = f"\n## {format_type} Summary {current_date}\n\n{content}\n"
            
            # Append to sent_summaries.md
            with open(summaries_file, 'a') as f:
                f.write(formatted_content)
            
            self.logger.info(f"Saved {format_type} summary to output/sent_summaries.md")
        except Exception as e:
            self.handle_error(e, {"context": f"Saving {format_type} summary"})

    def _add_call_to_action(self, summary: str) -> str:
        """Add call to action to the summary."""
        return f"{summary}\n\nJoin the discussion on Discord: https://discord.gg/ergo-platform-668903786361651200"
