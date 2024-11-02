#!/bin/bash
# Export full server history for specified time range

# Load configuration from config/.env file
source config/.env

# Constants
OUTPUT_DIR="./output"
EXPORTER="DiscordChatExporter/DiscordChatExporter-linux/mac/DiscordChatExporter.Cli.osx-arm64/DiscordChatExporter.Cli"

# Prompt user for time range in days
read -r -p "Enter the time range in days (e.g., 1 for 1 day, 7 for 7 days): " VALUE

# Validate input
if ! [[ "${VALUE}" =~ ^[0-9]+$ ]]; then
    echo "Invalid input. Please enter a numeric value for days."
    exit 1
fi

UNIT="d"
TIME_RANGE="${VALUE}${UNIT}"

# Calculate date range
AFTER_DATE=$(date -u -v-"${VALUE}"d '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
if [[ $? -ne 0 ]] || [[ -z "${AFTER_DATE}" ]]; then
	echo "Failed to calculate the date range. Please check the input format and try again."
	exit 1
fi
BEFORE_DATE=$(date -u '+%Y-%m-%d %H:%M:%S')

# Format dates for filenames
AFTER_DATE_FMT=$(date -u -j -f '%Y-%m-%d %H:%M:%S' "${AFTER_DATE}" '+%d%b' 2>/dev/null)
if [[ $? -ne 0 ]] || [[ -z "${AFTER_DATE_FMT}" ]]; then
	echo "Failed to format the after date. Please check the date settings."
	exit 1
fi
BEFORE_DATE_FMT=$(date -u '+%d%b')
CURRENT_TIME=$(date -u '+%H%M%S')

# Create export directory
EXPORT_DIR="${OUTPUT_DIR}/export-${DISCORD_SERVER_ID}-${AFTER_DATE_FMT}_${BEFORE_DATE_FMT}_${CURRENT_TIME}_${TIME_RANGE}"
mkdir -p "${EXPORT_DIR}"

# Export messages in JSON format
EXPORT_PATH="${EXPORT_DIR}/%G (export)/%C-%c-${AFTER_DATE_FMT}_${BEFORE_DATE_FMT}_${TIME_RANGE}.json"
echo "Exporting messages for the server in JSON format..."
chmod +x "${EXPORTER}"
"${EXPORTER}" exportguild \
	-t "${DISCORD_TOKEN}" \
	-g "${DISCORD_SERVER_ID}" \
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
