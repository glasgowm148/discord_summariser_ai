#!/bin/bash

# --- Configuration ---
if [ -f "config/.env" ]; then
    source "config/.env"
fi

if [ -z "${DISCORD_TOKEN}" ]; then
    echo "Error: DISCORD_TOKEN must be set in config/.env."
    exit 1
fi

GUILD_ID="${DISCORD_SERVER_ID:-668903786361651200}"
# Adjust the path to your DiscordChatExporter CLI executable if necessary
# Assuming it's relative to the project root where this script is run from
EXPORTER_PATH="./DiscordChatExporter/DiscordChatExporter-linux/mac/DiscordChatExporter.Cli.osx-arm64/DiscordChatExporter.Cli"
# Output directory for JSON exports (will be created if it doesn't exist)
EXPORT_DATE=$(date -u '+%Y-%m-%d')
EXPORT_DIR="./output/${EXPORT_DATE}/guild/last_week_export"
# Python script for extracting questions
PYTHON_SCRIPT="./scripts/extract_questions.py"
# Output file for the extracted questions
QUESTIONS_FILE="./output/${EXPORT_DATE}/questions_for_ama.txt"

# --- Calculate Date ---
# Get the date 7 days ago (macOS syntax)
START_DATE=$(date -v-7d '+%Y-%m-%d')
# For Linux, use: START_DATE=$(date -d "7 days ago" '+%Y-%m-%d')
# Uncomment the Linux line and comment the macOS line if you are on Linux.

echo "Exporting chats from Guild ID: $GUILD_ID since $START_DATE"
echo "Output directory: $EXPORT_DIR"
echo "Questions will be saved to: $QUESTIONS_FILE"

# --- Create Output Directory ---
mkdir -p "$EXPORT_DIR"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create output directory '$EXPORT_DIR'"
    exit 1
fi

# --- Run Exporter ---
# Check if the exporter executable exists
if [ ! -f "$EXPORTER_PATH" ]; then
    echo "Error: DiscordChatExporter executable not found at '$EXPORTER_PATH'"
    echo "Please check the EXPORTER_PATH variable in this script."
    exit 1
fi

echo "Running DiscordChatExporter..."
# Added trailing slash to EXPORT_DIR for the -o argument as required by the tool for guild exports
"$EXPORTER_PATH" exportguild -g "$GUILD_ID" --token "$DISCORD_TOKEN" --after "$START_DATE" --format Json -o "$EXPORT_DIR/"

if [ $? -ne 0 ]; then
    echo "Error: DiscordChatExporter failed."
    # Optionally exit here, or try to process any files that might have been exported
    # exit 1
fi

echo "Export finished."

# --- Extract Questions ---
# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python extraction script not found at '$PYTHON_SCRIPT'"
    exit 1
fi

echo "Extracting questions using $PYTHON_SCRIPT..."
# Ensure python3 is used, adjust if necessary for your system
python3 "$PYTHON_SCRIPT" "$EXPORT_DIR" > "$QUESTIONS_FILE"

if [ $? -ne 0 ]; then
    echo "Error: Question extraction failed."
    exit 1
fi

echo "Questions extracted successfully and saved to $QUESTIONS_FILE"
echo "Script finished."
exit 0
