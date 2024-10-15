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

# Check if the time range argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <time_range> (e.g., 1d, 7d, 1w, 5h) [server/channel]"
  exit 1
fi

# Calculate dates based on the provided time range
time_unit=${1: -1}
time_value=${1%[dwmh]}

case "$time_unit" in
  d) AFTER_DATE=$(date -u -d "$time_value days ago" '+%Y-%m-%d %H:%M:%S') ;;
  w) AFTER_DATE=$(date -u -d "$time_value weeks ago" '+%Y-%m-%d %H:%M:%S') ;;
  m) AFTER_DATE=$(date -u -d "$time_value months ago" '+%Y-%m-%d %H:%M:%S') ;;
  h) AFTER_DATE=$(date -u -d "$time_value hours ago" '+%Y-%m-%d %H:%M:%S') ;;
  *) echo "Invalid time range format. Use d (days), w (weeks), m (months), or h (hours)."; exit 1 ;;
esac

BEFORE_DATE=$(date -u '+%Y-%m-%d %H:%M:%S')
AFTER_DATE_FORMATTED=$(date -u -d "$AFTER_DATE" '+%d%b')
BEFORE_DATE_FORMATTED=$(date -u '+%d%b')

# Create the export directory based on the date range
EXPORT_DIR="$OUTPUT_BASE_DIR/export-server-${AFTER_DATE_FORMATTED}_${BEFORE_DATE_FORMATTED}"
mkdir -p "$EXPORT_DIR"

# Check if the export type argument is provided, otherwise ask the user
if [ -z "$2" ]; then
  read -p "Do you want to export the entire server or a specific channel? (enter 'server' or 'channel'): " EXPORT_TYPE
else
  EXPORT_TYPE=$2
fi

if [ "$EXPORT_TYPE" == "server" ]; then
  # Export all channels within the specified server
  echo "Exporting messages for the entire server"
  EXPORT_PATH="$EXPORT_DIR/%G/%C.html"
  $EXPORTER_PATH exportguild \
    -t "$DISCORD_TOKEN" \
    -g "$DISCORD_SERVER_ID" \
    --after "$AFTER_DATE" \
    --before "$BEFORE_DATE" \
    -o "$EXPORT_PATH" \
    --media \
    --format "$EXPORT_FORMAT"
  
  echo "Exported messages for the entire server have been written to the following files:"
  find "$EXPORT_DIR" -type f -name '*.html'
  echo "Running sanitise.py script for the entire server..."
  python3 sanitise.py --input-dir "$EXPORT_DIR"

elif [ "$EXPORT_TYPE" == "channel" ]; then
  # Check if the channel ID argument is provided, otherwise ask the user
  if [ -z "$3" ]; then
    read -p "Enter the channel ID to export: " CHANNEL_ID
  else
    CHANNEL_ID=$3
  fi
  # Export a specific channel
  echo "Exporting messages for channel ID: $CHANNEL_ID"
  EXPORT_PATH="$EXPORT_DIR/channel_$CHANNEL_ID.html"
  $EXPORTER_PATH export \
    -t "$DISCORD_TOKEN" \
    -c "$CHANNEL_ID" \
    --after "$AFTER_DATE" \
    --before "$BEFORE_DATE" \
    -o "$EXPORT_PATH" \
    --media \
    --format "$EXPORT_FORMAT"
  echo "Exported messages for channel ID: $CHANNEL_ID have been written to the file:"
  echo "$EXPORT_PATH"
  echo "Running sanitise.py script for channel ID: $CHANNEL_ID..."
  python3 sanitise.py --input-dir "$EXPORT_DIR/channel_$CHANNEL_ID.html"
else
  echo "Invalid option. Please enter 'server' or 'channel'."
  exit 1
fi
