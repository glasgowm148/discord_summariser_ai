# Chat Summariser

A tool to export, process, and summarize Discord chat messages with multi-language support and social media integration.

## Project Structure

```
chat_summariser/
├── config/                 # Configuration files
│   ├── .env               # Environment variables (gitignored)
│   └── .env.example       # Example environment file
├── models/                # Data models
│   └── discord_message.py # Discord message model
├── output/                # Generated outputs
├── scripts/               # Shell scripts
│   └── export_chat.sh     # Discord chat export script
├── services/             # Core services
│   ├── csv_loader.py     # CSV file handling
│   ├── discord_service.py # Discord integration
│   ├── json_cleaner.py   # JSON processing
│   ├── summary_generator.py # Summary generation
│   └── twitter_service.py # Twitter integration
├── utils/                # Utility functions
│   ├── logging_config.py # Logging configuration
│   └── prompts.py       # OpenAI prompts
└── summarise.py         # Main application entry
```

## Setup

1. Clone the repository
2. Copy `config/.env.example` to `config/.env` and fill in your values
3. Install dependencies: `pip install -r requirements.txt`

## Usage

1. Export chat messages:
   ```bash
   ./scripts/export_chat.sh 1d  # Export last day
   ./scripts/export_chat.sh 1w  # Export last week
   ```

2. Generate summary:
   ```bash
   python summarise.py
   ```

The tool will:
- Process the exported chat messages
- Generate a summary using OpenAI
- Post to Discord (with translations)
- Optionally post to Twitter

## Features

- Discord chat export and processing
- Multi-language summaries (via OpenAI)
- Discord webhook integration
- Twitter integration
- Configurable time ranges
- Detailed logging
