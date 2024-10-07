#!/bin/bash

# Configuration Variables
source .env

# Discord token (keep this secure and do not share)
DISCORD_TOKEN=$DISCORD_TOKEN

# Use the OPENAI_API_KEY from the .env file
OPENAI_API_KEY=$OPENAI_API_KEY

# Output base directory for the exported chat logs
OUTPUT_BASE_DIR="./output"

# Path to DiscordChatExporter.Cli executable
EXPORTER_PATH="DiscordChatExporter/DiscordChatExporter.Cli"

# Export format (e.g., PlainText, HtmlDark)
EXPORT_FORMAT="HtmlDark"

# Calculate dates for the past week
AFTER_DATE=$(date -u -d "7 days ago" '+%Y-%m-%d %H:%M:%S')
BEFORE_DATE=$(date -u '+%Y-%m-%d %H:%M:%S')
AFTER_DATE_FORMATTED=$(date -u -d "7 days ago" '+%d%b')
BEFORE_DATE_FORMATTED=$(date -u '+%d%b')

# Create the export directory based on the date range
EXPORT_DIR="$OUTPUT_BASE_DIR/export-server-${AFTER_DATE_FORMATTED}_${BEFORE_DATE_FORMATTED}"
mkdir -p "$EXPORT_DIR"

# Ask the user if they want to export the entire server or a specific channel
read -p "Do you want to export the entire server or a specific channel? (enter 'server' or 'channel'): " EXPORT_TYPE

if [ "$EXPORT_TYPE" == "server" ]; then
  # Export all channels within the specified server
  echo "Exporting messages for the entire server"
  $EXPORTER_PATH exportguild \
    -t "$DISCORD_TOKEN" \
    -g "$DISCORD_SERVER_ID" \
    --after "$AFTER_DATE" \
    --before "$BEFORE_DATE" \
    -o "$EXPORT_DIR/%G/%C.html" \
    --media \
    --format "$EXPORT_FORMAT"

elif [ "$EXPORT_TYPE" == "channel" ]; then
  # Ask for the channel ID
  read -p "Enter the channel ID to export: " CHANNEL_ID
  # Export a specific channel
  echo "Exporting messages for channel ID: $CHANNEL_ID"
  $EXPORTER_PATH export \
    -t "$DISCORD_TOKEN" \
    -c "$CHANNEL_ID" \
    --after "$AFTER_DATE" \
    --before "$BEFORE_DATE" \
    -o "$EXPORT_DIR/channel_$CHANNEL_ID.html" \
    --media \
    --format "$EXPORT_FORMAT"
else
  echo "Invalid option. Please enter 'server' or 'channel'."
  exit 1
fi