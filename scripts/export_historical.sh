#!/bin/bash

# Load configuration from config/.env file
source config/.env

# Create historical directory
mkdir -p output/historical

# Export general development channel
channel_id="669989266478202917"
channel_name="development"
days=10
#365

echo "Exporting ${channel_name} for the past ${days} days..."

# Temporarily modify DISCORD_CHANNEL_ID for export_chat.sh
original_channel_id=$DISCORD_CHANNEL_ID
export DISCORD_CHANNEL_ID=$channel_id

# Run export_chat.sh with 365 days range
bash ./scripts/export_chat.sh ${days}d

# Move the exported files to historical directory
latest_export=$(ls -td output/export-* | head -1)
if [ -d "$latest_export" ]; then
    # Find the CSV file
    csv_file=$(find "$latest_export" -name "*.csv")
    if [ -n "$csv_file" ]; then
        # Move and rename the CSV file
        mv "$csv_file" "output/historical/${channel_name}_${channel_id}.csv"
        echo "Successfully exported ${channel_name}"
    else
        echo "No CSV file found for ${channel_name}"
    fi
    # Clean up the export directory
    rm -rf "$latest_export"
else
    echo "Export failed for ${channel_name}"
fi

# Restore original channel ID
export DISCORD_CHANNEL_ID=$original_channel_id

echo "Export completed. Files saved in output/historical/"
