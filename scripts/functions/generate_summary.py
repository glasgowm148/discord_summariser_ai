# generate_summary.py
import os
import re
import time
import openai
from datetime import datetime
from pathlib import Path

def generate_summary(content, days_covered):
    system_prompt = (
        "You are an assistant tasked with creating a concise and focused summary from a CSV of Discord messages. "
        "The summaries should highlight recent developments and discussions within the Ergo ecosystem. "
        "Ensure all provided Discord message links are retained and correctly used in the corresponding bullet points, reflecting accurate channel and message IDs without repetition. "
        "Exclude topics such as token requests, migration, and unrelated projects. "
        "Treat messages containing 'Weekly Update' as special, referencing them appropriately and only once as their own bullet point titled 'Weekly update'. "
        "Avoid general mentions of community engagement or collaboration unless they are tied to a new and specific update. "
        "Each point must be clear and directly relevant to Ergo’s current advancements."
    )

    # Load previous summaries to avoid repetition
    previous_summaries = load_previous_summaries()

    tweet_prompt = (
        f"Summarize the last {days_covered} days of Discord messages into 10-15 bullet points, each focusing exclusively on specific, actionable updates about Ergo’s technical progress and community projects. "
        f"Begin the summary with `## Summary of discussions over the past {days_covered} days:` followed by bullet points. "
        "Ensure each bullet point includes a markdown link embedded directly within the relevant text, such as: - 🛠️ Ledger Integration: [Ledger Stax and Flex integration](https://discord.com/channels/discord_server_id/channel_id/msg_id) is reportedly complete. "        
        "Include varied updates from several different channels, ensuring some bullets from less active channels are included, and avoid repeating any points. "
        "Aim to have at least one bullet for each active channel if possible. "
        "Do not make assumptions about what acronyms stand for. "
        "Avoid extra line breaks between the bullets. "
        "Exclude topics related to token requests, migration, moderation, and general community collaboration without specific context. "
        "Use concise language and incorporate engaging emojis, focusing only on points that reflect recent, tangible developments within Ergo's ecosystem. "
        "Avoid speculative language or references to unrelated projects. Each point should be relevant, informative, and free from unnecessary details. "
        "Include only verifiable facts and specific details directly from the summaries; avoid generalizations. "
        "Break down complex ideas into smaller, straightforward sentences without adding interpretations. "
        "Avoid vague terms or embellishments that might introduce uncertainty, such as phrases like 'indicating active contributions from the community.' "
        "There is no need for a vague conclusion or summary line at the end. "
        "Rephrase any technical terms clearly but accurately to ensure comprehension without altering meaning. "
        "Double-check all project names, commands, and URLs to prevent inaccuracies.\n\n"
        f"{content}\n\nPrevious Summaries for Reference:\n{''.join(previous_summaries)}"
    )

    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": tweet_prompt}
                ],
                temperature=0.6,
                max_tokens=1500
            )
            summary = response.model_dump()["choices"][0]["message"]["content"]

            summary = re.sub(r'\(Note:.*?\)', '', summary, flags=re.DOTALL)
            summary = summary.replace('@', '').replace('**', '')

            summary_with_call_to_action = summary + f"\n\nJoin the discussion on Discord: {os.getenv('DISCORD_INVITE_LINK')}"

            bullet_points = [bullet for bullet in summary.split("\n") if bullet.strip().startswith("-") and "https://discord.com/channels" in bullet]
            if len(bullet_points) >= 5:
                print("Summary generated successfully.")
                log_sent_summary(summary)
                return summary.strip(), summary_with_call_to_action.strip()
            else:
                print("Summary does not have at least 5 bullet points with URLs. Retrying...\n\n")
                retry_count += 1
                time.sleep(1)

        except Exception as e:
            print(f"Error generating summary: {e}")
            retry_count += 1
            time.sleep(1)

    print("Failed to generate a summary containing URLs for each bullet point after several attempts.")
    return None, None

def log_sent_summary(summary):
    log_file = Path('sent_summaries.md')
    date_header = f"\n# {datetime.now().strftime('%Y-%m-%d')}\n"
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(date_header)
            f.write(f"- {summary}\n")
        print("Summary logged successfully.")
    except Exception as e:
        print(f"Failed to log summary: {e}")

def load_previous_summaries():
    log_file = Path('sent_summaries.md')
    if not log_file.exists():
        return []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"Failed to load previous summaries: {e}")
        return []
