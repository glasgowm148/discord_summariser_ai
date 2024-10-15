# prepare_summary_content.py
import json
import os

def prepare_summary_content(df):
    timeframe_intro = "Ergo Community Highlights from the past 24 hours:\n"
    content_data = []

    discord_server_id = os.getenv("DISCORD_SERVER_ID")

    for _, row in df.iterrows():
        author = row['author_name']
        msg = row['message_content']
        timestamp = row['message_timestamp']
        channel_id = row['channel_id']
        msg_id = row['message_id']
        link = f"https://discord.com/channels/{discord_server_id}/{channel_id}/{msg_id}"
        
        weight = row['message_reactions_count'] + row['message_mentions_count']
        role_positions = json.loads(row['role_position'])
        if role_positions:
            weight += 1 / min(role_positions)

        content_data.append((weight, f"{author} ({timestamp}): {msg} ({link})"))

    content_data.sort(reverse=True, key=lambda x: x[0])
    max_messages = 10000
    content_data = [entry[1] for entry in content_data[:max_messages]]

    if not content_data:
        raise ValueError("No relevant data to summarize.")

    return timeframe_intro + "\n".join(content_data)
