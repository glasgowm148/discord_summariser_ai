#!/bin/bash

# Configuration Variables

source .env

# Discord token (keep this secure and do not share)
DISCORD_TOKEN=$DISCORD_TOKEN

# Use the OPENAI_API_KEY from the .env file

OPENAI_API_KEY=$OPENAI_API_KEY

# Channel ID for the development channel
CHANNEL_ID="669989266478202917"

# Output directory for the exported chat logs
OUTPUT_DIR="./output"

# Path to DiscordChatExporter.Cli executable
EXPORTER_PATH="DiscordChatExporter/DiscordChatExporter.Cli"

# Export format (e.g., PlainText, HtmlDark)
EXPORT_FORMAT="HtmlDark"

# Calculate dates for the previous Wednesday and Thursday
# This ensures we capture the chat from last Wednesday
# The script should be scheduled to run every Thursday after the dev chat

# Calculate dates for yesterday (Wednesday) and today (Thursday)
#AFTER_DATE=$(date -u -d "yesterday 00:00:00" '+%Y-%m-%d %H:%M:%S')
#BEFORE_DATE=$(date -u -d "today 00:00:00" '+%Y-%m-%d %H:%M:%S')

# Calculate dates for the last 24 hours
#AFTER_DATE=$(date -u -d "24 hours ago" '+%Y-%m-%d %H:%M:%S')
# Calculate dates for the last week
AFTER_DATE=$(date -u -d "7 days ago" '+%Y-%m-%d %H:%M:%S')
BEFORE_DATE=$(date -u '+%Y-%m-%d %H:%M:%S')


# Run the export command
$EXPORTER_PATH export \
    -t "$DISCORD_TOKEN" \
    -c "$CHANNEL_ID" \
    --after "$AFTER_DATE" \
    --before "$BEFORE_DATE" \
    -o "$OUTPUT_DIR" \
    --media \
    --format "$EXPORT_FORMAT"

# Check if the export was successful
if [ $? -eq 0 ]; then
    echo "Export completed successfully."

    # Proceed to summarize and send to Discord
    python3 process_and_send_summary.py
else
    echo "Export failed."
fi
