#!/bin/bash
# Export 1 year of development channel history

# Load configuration from config/.env file
if [ -f "config/.env" ]; then
    source "config/.env"
fi

if [ -z "${DISCORD_TOKEN}" ] || [ -z "${DISCORD_SERVER_ID}" ]; then
    echo "Error: DISCORD_TOKEN and DISCORD_SERVER_ID must be set in config/.env."
    exit 1
fi

# Constants
EXPORT_DATE=$(date -u '+%Y-%m-%d')
OUTPUT_DIR="./output/${EXPORT_DATE}"
EXPORTER="DiscordChatExporter/DiscordChatExporter-linux/mac/DiscordChatExporter.Cli.osx-arm64/DiscordChatExporter.Cli"
DEV_CHANNEL="669989266478202917"

# Create historical directory
mkdir -p "${OUTPUT_DIR}/historical"

# Calculate date range (1 year)
AFTER_DATE=$(date -u -v-365d '+%Y-%m-%d %H:%M:%S')
BEFORE_DATE=$(date -u '+%Y-%m-%d %H:%M:%S')

# Format dates for filenames
AFTER_DATE_FMT=$(date -u -j -f '%Y-%m-%d %H:%M:%S' "${AFTER_DATE}" '+%d%b')
BEFORE_DATE_FMT=$(date -u '+%d%b')
CURRENT_TIME=$(date -u '+%H%M%S')

# Create export directory
EXPORT_DIR="${OUTPUT_DIR}/export-${DISCORD_SERVER_ID}-${AFTER_DATE_FMT}_${BEFORE_DATE_FMT}_${CURRENT_TIME}_365d"
mkdir -p "${EXPORT_DIR}"

# Export messages in JSON format
EXPORT_PATH="${EXPORT_DIR}/%G (export)/%C-%c-${AFTER_DATE_FMT}_${BEFORE_DATE_FMT}_365d.json"
echo "Exporting messages for development channel..."
chmod +x "${EXPORTER}"
"${EXPORTER}" export \
    -t "${DISCORD_TOKEN}" \
    -c "${DEV_CHANNEL}" \
    --after "${AFTER_DATE}" \
    --before "${BEFORE_DATE}" \
    -o "${EXPORT_PATH}" \
    --format "Json"

if [[ $? -ne 0 ]]; then
    echo "Failed to execute DiscordChatExporter. Please check permissions or path."
    exit 1
fi

echo "Export completed. Files:"
find "${EXPORT_DIR}" -type f -name "*.json"

# Run the JSON cleaning script
echo "Running JSON cleaning script..."
python3 scripts/clean_export.py "${EXPORT_DIR}" \
    --historical-output "${OUTPUT_DIR}/historical/development_${DEV_CHANNEL}.csv" \
    --cleanup-export-dir
echo "JSON cleaning completed."

echo "Export completed. Files saved in ${OUTPUT_DIR}/historical/"
