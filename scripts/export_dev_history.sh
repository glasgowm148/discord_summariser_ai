#!/bin/bash
# Export 1 year of development channel history

# Load configuration from config/.env file
source config/.env

# Constants
OUTPUT_DIR="./output"
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
python3 -c "
from services.json_cleaner import JsonCleanerService
import os

cleaner = JsonCleanerService()
json_files, search_dir = cleaner.get_json_files('${EXPORT_DIR}')
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
    with open(os.path.join(search_dir, 'error_log.txt'), 'w') as error_file:
        error_file.write('\n'.join(error_log))
"
echo "JSON cleaning completed."

# Move the CSV file to historical directory
csv_file=$(find "${EXPORT_DIR}" -name "*.csv")
if [ -n "$csv_file" ]; then
    mv "$csv_file" "${OUTPUT_DIR}/historical/development_${DEV_CHANNEL}.csv"
    echo "Successfully exported development channel"
else
    echo "No CSV file found for development channel"
fi

# Clean up the export directory
rm -rf "${EXPORT_DIR}"

echo "Export completed. Files saved in output/historical/"
