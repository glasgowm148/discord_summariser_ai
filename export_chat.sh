#!/bin/bash
# Reference: https://github.com/Tyrrrz/DiscordChatExporter/blob/master/.docs/Using-the-CLI.md

# Load configuration from .env file
source .env

# Constants
OUTPUT_DIR="./output"
EXPORTER="DiscordChatExporter/DiscordChatExporter.Cli"
DEFAULT_RANGE="1d"

# Get time range from argument or use default
TIME_RANGE="${1:-$DEFAULT_RANGE}"
UNIT="${TIME_RANGE: -1}"
VALUE="${TIME_RANGE%[dwmh]}"

# Validate and convert time unit
case "$UNIT" in
  d) UNIT_NAME="days" ;;
  w) UNIT_NAME="weeks" ;;
  m) UNIT_NAME="months" ;;
  h) UNIT_NAME="hours" ;;
  *)
    echo "Invalid time unit. Use d (days), w (weeks), m (months), or h (hours)."
    exit 1
    ;;
esac

# Calculate date range
AFTER_DATE=$(date -u -d "$VALUE $UNIT_NAME ago" '+%Y-%m-%d %H:%M:%S')
BEFORE_DATE=$(date -u '+%Y-%m-%d %H:%M:%S')

# Format dates for filenames
AFTER_DATE_FMT=$(date -u -d "$AFTER_DATE" '+%d%b')
BEFORE_DATE_FMT=$(date -u '+%d%b')
CURRENT_TIME=$(date -u '+%H%M%S')

# Create export directory
EXPORT_DIR="$OUTPUT_DIR/export-${DISCORD_SERVER_ID}-${AFTER_DATE_FMT}_${BEFORE_DATE_FMT}_${CURRENT_TIME}_${TIME_RANGE}"
mkdir -p "$EXPORT_DIR"

# Export messages in JSON format
EXPORT_PATH="$EXPORT_DIR/%G (export)/%C-%c-${AFTER_DATE_FMT}_${BEFORE_DATE_FMT}_${TIME_RANGE}.json"
echo "Exporting messages for the server in JSON format..."
$EXPORTER exportguild \
  -t "$DISCORD_TOKEN" \
  -g "$DISCORD_SERVER_ID" \
  --after "$AFTER_DATE" \
  --before "$BEFORE_DATE" \
  -o "$EXPORT_PATH" \
  --format "Json"

echo "Export completed. Files:"
find "$EXPORT_DIR" -type f -name "*.json"

# Run the clean_json.py script
echo "Running clean_json.py script..."
python3 functions/clean_json.py --input-dir "$EXPORT_DIR"
echo "clean_json.py script execution completed."
