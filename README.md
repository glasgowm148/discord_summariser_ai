# Discord Chat Summarizer AI

A sophisticated Python application that transforms Discord chat conversations into concise, intelligent summaries using advanced AI processing and OpenAI's GPT models.

## Project Structure

```bash
discord_summariser_ai/
├── config/
│   ├── .env.example
│   ├── README.md
│   └── settings.py
├── helpers/
│   ├── formatters/
│   │   ├── content_formatter.py
│   │   └── social_media_formatter.py
│   ├── processors/
│   │   ├── bullet_processor.py
│   │   ├── bullet_validator.py
│   │   ├── chunk_optimizer.py
│   │   ├── chunk_processor.py
│   │   ├── content_relationship_analyzer.py
│   │   ├── discord_link_processor.py
│   │   ├── text_cleaner.py
│   │   └── text_processor.py
│   └── validators/
│       └── content_validator.py
├── models/
│   ├── bullet_point.py
│   ├── discord_message.py
│   └── project.py
├── services/
│   ├── base_service.py
│   ├── csv_loader.py
│   ├── hackmd_service.py
│   ├── json_cleaner.py
│   ├── meta_service.py
│   ├── project_manager.py
│   ├── service_factory.py
│   ├── summary_finalizer.py
│   ├── summary_generator.py
│   ├── text_processor.py
│   └── social_media/
│       ├── discord_service.py
│       ├── reddit_service.py
│       └── twitter_service.py
├── utils/
│   ├── logging_config.py
│   └── prompts.py
├── scripts/
│   ├── build_knowledge_base.py
│   ├── export_channel.sh
│   ├── export_chat.sh
│   ├── export_dev_history.sh
│   ├── export_historical.sh
│   └── export_server.sh
└── summarise.py
```

## Advanced Features

- Intelligent Discord chat export processing
- Multi-stage AI-powered summarization
- Advanced content relationship analysis
- Bullet point validation and optimization
- Support for multiple export scenarios (channel, server, historical)
- Flexible social media distribution (Discord, Twitter, Reddit)
- Robust error handling and logging
- Configurable AI processing parameters

## Key Processing Components

- **Content Processors**: Sophisticated text cleaning, chunk optimization, and relationship analysis
- **Validators**: Ensure summary quality and coherence
- **Formatters**: Adapt summaries for different platforms
- **Social Media Services**: Distribute summaries across multiple channels

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

4. Configure environment variables:
```bash
cp config/.env.example config/.env
```

5. Edit `config/.env` with your API keys and settings:
```bash
OPENAI_API_KEY=your_openai_api_key
TWITTER_CONSUMER_KEY=your_twitter_consumer_key
DISCORD_WEBHOOK_URL=your_discord_webhook_url
```

## Usage

1. Export Discord chat using flexible export scripts:
```bash
# Export entire channel
./scripts/export_channel.sh

# Export server history
./scripts/export_server.sh

# Export specific time range
./scripts/export_historical.sh
```

2. Run the summarizer:
```bash
python summarise.py
```

The application will:
- Load and process the latest chat export
- Generate an intelligent, context-aware summary
- Distribute to configured platforms
- Log detailed processing information

## Architecture

Modular, service-oriented design with:
- Separation of concerns
- Extensible processing pipeline
- Configurable AI summarization strategies
- Multi-platform support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is distributed under a custom non-commercial license. Unauthorized commercial use is prohibited. For commercial inquiries or permissions, please contact us in writing.
