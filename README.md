# Discord Chat Summarizer

A Python application that summarizes Discord chat conversations using OpenAI's GPT models. The summarizer processes chat exports, generates concise bullet-point summaries, and can distribute them to Discord and Twitter.

## Project Structure

```
discord_summariser_ai/
├── config/
│   ├── .env.example
│   ├── README.md
│   └── settings.py
├── models/
│   └── discord_message.py
├── services/
│   ├── base_service.py
│   ├── bullet_processor.py
│   ├── chunk_processor.py
│   ├── csv_loader.py
│   ├── discord_service.py
│   ├── json_cleaner.py
│   ├── summary_finalizer.py
│   ├── summary_generator.py
│   └── twitter_service.py
├── utils/
│   ├── logging_config.py
│   └── prompts.py
├── scripts/
│   └── export_chat.sh
├── output/
├── .gitignore
├── README.md
└── summarise.py
```

## Features

- Processes Discord chat exports in CSV format
- Generates concise, bullet-point summaries using OpenAI's GPT models
- Supports both daily and weekly summaries
- Posts summaries to Discord via webhooks
- Optional Twitter integration for sharing summaries
- Robust error handling and logging
- Configurable settings and environment variables

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/discord_summariser_ai.git
cd discord_summariser_ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp config/.env.example config/.env
```

5. Edit `config/.env` with your API keys and settings:
```
OPENAI_API_KEY=your_openai_api_key
TWITTER_CONSUMER_KEY=your_twitter_consumer_key
TWITTER_CONSUMER_SECRET=your_twitter_consumer_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
DISCORD_WEBHOOK_URL=your_discord_webhook_url
```

## Usage

1. Export Discord chat using the provided script:
```bash
./scripts/export_chat.sh
```

2. Run the summarizer:
```bash
python summarise.py
```

The script will:
1. Load the latest chat export from the `output` directory
2. Generate a summary using OpenAI's GPT models
3. Post the summary to Discord
4. Optionally post to Twitter if confirmed

## Architecture

The application follows a service-oriented architecture with clear separation of concerns:

- **Base Service**: Provides common functionality for error handling and logging
- **Services**: Individual components handle specific tasks (CSV loading, summary generation, etc.)
- **Models**: Data structures for representing Discord messages and other entities
- **Utils**: Helper functions and configuration
- **Config**: Central location for settings and environment variables

## Error Handling

The application includes comprehensive error handling:
- Validates environment variables and configurations
- Handles API errors gracefully
- Provides detailed logging
- Implements retry mechanisms for API calls
- Validates input data and generated content

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is distributed under a custom non-commercial license. Unauthorized commercial use is prohibited. For commercial inquiries or permissions, please contact us in writing.