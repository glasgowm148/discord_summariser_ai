#!/bin/bash

# Description: This script executes the full workflow: exporting chat logs, sanitizing them, and processing the summary.

# Step 1: Run export_chat.sh to export the chat logs
if scripts/export_chat.sh; then
    echo "Chat logs exported successfully."
else
    echo "Failed to export chat logs. Exiting."
    exit 1
fi

# Step 2: Run sanitise.py to clean up the exported chat logs
if python3 scripts/sanitise.py; then
    echo "Chat logs sanitized successfully."
else
    echo "Failed to sanitize chat logs. Exiting."
    exit 1
fi

# Step 3: Run process_and_send_summary.py to process and send the summary to Discord
if python3 scripts/process_and_send_summary.py; then
    echo "Summary processed and sent to Discord successfully."
else
    echo "Failed to process and send summary to Discord. Exiting."
    exit 1
fi