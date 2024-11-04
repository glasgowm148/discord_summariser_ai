"""Finalize and format summaries for different platforms."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Set
from difflib import SequenceMatcher

from openai import OpenAI

from config.settings import OUTPUT_DIR
from services.base_service import BaseService
from services.project_manager import ProjectManager
from utils.prompts import SummaryPrompts


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
                self._save_to_sent_summaries(
                    "Discord with CTA", discord_summary_with_cta
                )
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
        try:
            # Create section header
            header = f"## Updates from the Past {days_covered} Days"
            
            # Format bullets with proper spacing and ensure no duplicates
            formatted_bullets = []
            seen_urls: Set[str] = set()
            
            for bullet in unique_bullets:
                # Extract Discord URL from the bullet
                url_match = re.search(r'https://discord\.com/channels/\d+/\d+/\d+', bullet)
                if url_match:
                    url = url_match.group(0)
                    if url not in seen_urls:
                        # Preserve any existing emoji
                        emoji_match = re.match(r'^- ([^\w\s]) ', bullet)
                        if not emoji_match:
                            # If no emoji found, let the model add one through the prompt
                            bullet = f"- {bullet[2:].strip()}"
                        formatted_bullets.append(bullet)
                        seen_urls.add(url)
                else:
                    # If no URL found, include the bullet preserving any emoji
                    emoji_match = re.match(r'^- ([^\w\s]) ', bullet)
                    if not emoji_match:
                        # If no emoji found, let the model add one through the prompt
                        bullet = f"- {bullet[2:].strip()}"
                    formatted_bullets.append(bullet)
            
            # Join all parts together
            final_summary = f"{header}\n" + "\n".join(formatted_bullets)
            
            # Create version with call to action
            summary_with_cta = self._add_call_to_action(final_summary)
            
            return final_summary, summary_with_cta
            
        except Exception as e:
            self.handle_error(e, {"context": "Creating Discord summary"})
            return None, None

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
                        "content": "You are a technical writer for the Ergo blockchain platform. Your task is to create a detailed Reddit summary. IMPORTANT: When including Discord links, use the exact channel_id and message_id from the original bullet points - do not modify these IDs.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.7,
                max_tokens=4000,
            )

            reddit_content = response.choices[0].message.content
            if not any(
                line.strip().startswith("#") for line in reddit_content.split("\n")
            ):
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

    def format_for_facebook(self, summary: str) -> str:
        """Format the summary to be Facebook-friendly with appropriate formatting and links."""
        try:
            formatted_lines = []
            for line in summary.split("\n"):
                if not line.strip():
                    continue

                # Convert section headers to Facebook-style formatting
                if line.startswith("#"):
                    line = line.lstrip("#").strip().upper()
                    formatted_lines.extend(["", "📢 " + line, ""])
                    continue

                # Process bullet points
                if line.startswith("-"):
                    # Keep bold formatting for project names
                    line = line.lstrip("- ").strip()

                    # Convert Discord links to a more readable format
                    line = re.sub(
                        r"\(https://discord\.com/channels/[^)]+\)",
                        "(View full discussion on Discord)",
                        line,
                    )

                    # Add bullet point emoji
                    formatted_lines.append("• " + line)
                else:
                    formatted_lines.append(line)

            formatted_summary = "\n".join(formatted_lines).strip()

            # Add Facebook-specific call to action
            formatted_summary += "\n\n🔗 Join our Discord community for real-time updates and discussions: https://discord.gg/ergo-platform-668903786361651200"

            return formatted_summary

        except Exception as e:
            self.handle_error(e, {"context": "Formatting for Facebook"})
            return summary

    def format_for_instagram(self, summary: str) -> str:
        """Format the summary to be Instagram-friendly with appropriate formatting and hashtags."""
        try:
            formatted_lines = []
            for line in summary.split("\n"):
                if not line.strip():
                    continue

                # Convert section headers to Instagram-style formatting
                if line.startswith("#"):
                    line = line.lstrip("#").strip().upper()
                    formatted_lines.extend(["", "🚀 " + line + " 🚀", ""])
                    continue

                # Process bullet points
                if line.startswith("-"):
                    # Keep bold formatting for project names
                    line = line.lstrip("- ").strip()

                    # Remove Discord links but keep the text
                    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
                    line = re.sub(r"\(https://discord\.com/channels/[^)]+\)", "", line)

                    # Add varied bullet point emojis
                    bullet_emojis = ["💫", "✨", "🔸", "📌"]
                    emoji = bullet_emojis[len(formatted_lines) % len(bullet_emojis)]
                    formatted_lines.append(f"{emoji} {line}")
                else:
                    formatted_lines.append(line)

            formatted_summary = "\n".join(formatted_lines).strip()

            # Add Instagram-specific hashtags
            hashtags = "\n\n.\n.\n.\n#Ergo #Blockchain #Cryptocurrency #CryptoNews #BlockchainDevelopment #DeFi #CryptoTechnology #Ergonauts #CryptoInnovation #BlockchainInnovation #CryptoUpdates #BlockchainUpdates"
            formatted_summary += hashtags

            # Add Instagram-specific call to action
            formatted_summary += (
                "\n\n💫 Join our Discord community for real-time updates! Link in bio."
            )

            return formatted_summary

        except Exception as e:
            self.handle_error(e, {"context": "Formatting for Instagram"})
            return summary

    def _remove_duplicate_bullets(self, bullets: List[str]) -> List[str]:
        """Remove duplicate bullets while preserving the most informative version."""
        def extract_core_content(bullet: str) -> str:
            """Extract core content by removing formatting, links, and common variations."""
            # Remove emojis, links, and formatting
            content = re.sub(r'^- [^\w\s] ', '- ', bullet)  # Remove emoji but preserve the dash
            content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
            content = re.sub(r'\(https://discord\.com/channels/[^)]+\)', '', content)
            
            # Remove common prefixes and suffixes
            content = re.sub(r'^- ', '', content)
            content = re.sub(r'(?i)(read more|explore|view|catch|delve|find out) (?:more |this |the )?(here|discussion|details|conversation|insights?|development)\.?$', '', content)
            
            # Normalize whitespace
            content = ' '.join(content.split())
            return content.lower().strip()

        def extract_discord_url(bullet: str) -> Optional[str]:
            """Extract Discord URL from a bullet point."""
            match = re.search(r'https://discord\.com/channels/\d+/\d+/\d+', bullet)
            return match.group(0) if match else None

        def are_similar(text1: str, text2: str, threshold: float = 0.85) -> bool:
            """Check if two texts are similar using sequence matcher."""
            return SequenceMatcher(None, text1, text2).ratio() > threshold

        def get_info_score(bullet: str) -> int:
            """Calculate an information score for a bullet point."""
            # More words generally means more information
            word_count = len(bullet.split())
            # Presence of specific details increases score
            has_numbers = 1 if re.search(r'\d', bullet) else 0
            has_quotes = 2 if '"' in bullet or "'" in bullet else 0
            has_technical_terms = 2 if re.search(r'(?i)(implementation|development|infrastructure|protocol|system|platform)', bullet) else 0
            return word_count + has_numbers + has_quotes + has_technical_terms

        unique_bullets = []
        processed_contents = []
        seen_urls = set()

        for bullet in bullets:
            core_content = extract_core_content(bullet)
            discord_url = extract_discord_url(bullet)
            
            # Skip if empty after processing
            if not core_content:
                continue
            
            # Skip if URL already seen
            if discord_url and discord_url in seen_urls:
                continue
                
            # Check if we have a similar bullet
            is_duplicate = False
            for idx, existing_content in enumerate(processed_contents):
                if are_similar(core_content, existing_content):
                    # If this version is more informative, replace the existing one
                    if get_info_score(bullet) > get_info_score(unique_bullets[idx]):
                        # Remove old URL from seen_urls if it exists
                        old_url = extract_discord_url(unique_bullets[idx])
                        if old_url:
                            seen_urls.remove(old_url)
                        # Add new bullet and URL
                        unique_bullets[idx] = bullet
                        if discord_url:
                            seen_urls.add(discord_url)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_bullets.append(bullet)
                processed_contents.append(core_content)
                if discord_url:
                    seen_urls.add(discord_url)

        return unique_bullets

    def _clean_final_summary(self, summary: str) -> str:
        """Clean and validate the final summary."""
        # Remove any notes or comments
        summary = re.sub(r"\(Note:.*?\)", "", summary, flags=re.DOTALL)
        summary = re.sub(r"\n\s*\n", "\n", summary)

        # Process each line
        valid_sections = []
        seen_urls = set()
        
        for line in summary.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("#"):
                valid_sections.append(line)
            elif line.startswith("-"):
                # Check for Discord URL
                url_match = re.search(r'https://discord\.com/channels/\d+/\d+/\d+', line)
                if url_match:
                    url = url_match.group(0)
                    if url not in seen_urls:
                        valid_sections.append(line)
                        seen_urls.add(url)
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

            summaries_file = output_dir / "sent_summaries.md"
            current_date = datetime.now().strftime("%Y-%m-%d")
            formatted_content = (
                f"\n## {format_type} Summary {current_date}\n\n{content}\n"
            )

            # Append to sent_summaries.md
            with open(summaries_file, "a") as f:
                f.write(formatted_content)

            self.logger.info(f"Saved {format_type} summary to output/sent_summaries.md")
        except Exception as e:
            self.handle_error(e, {"context": f"Saving {format_type} summary"})

    def _add_call_to_action(self, summary: str) -> str:
        """Add call to action to the summary."""
        return f"{summary}\n\nJoin the discussion on Discord: https://discord.gg/ergo-platform-668903786361651200"
