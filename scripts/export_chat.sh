#!/bin/bash
# Reference: https://github.com/Tyrrrz/DiscordChatExporter/blob/master/.docs/Using-the-CLI.md

# Load configuration from config/.env file
source config/.env

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

# Run the JSON cleaning script
echo "Running JSON cleaning script..."
python3 -c "
from services.json_cleaner import JsonCleanerService
cleaner = JsonCleanerService()
json_files, search_dir = cleaner.get_json_files('$EXPORT_DIR')
all_cleaned_data = []
error_log = []

for json_file in json_files:
    print(f'Processing JSON file: {json_file}')
    try:
        with open(json_file, 'r') as f:
            data = __import__('json').load(f)
        cleaned_data = cleaner.clean_chatlog_data(data)
        all_cleaned_data.extend(cleaned_data)
    except Exception as e:
        error_message = f'Error processing file {json_file}: {e}'
        print(error_message)
        error_log.append(error_message)

if all_cleaned_data:
    cleaner.save_json(all_cleaned_data, search_dir)
    days_covered = cleaner.get_days_covered(all_cleaned_data)
    cleaner.save_csv(all_cleaned_data, search_dir, days_covered)
    cleaner.print_stats(all_cleaned_data)

if error_log:
    with open(f'{search_dir}/error_log.txt', 'w') as error_file:
        error_file.write('\n'.join(error_log))
"
echo "JSON cleaning completed."
