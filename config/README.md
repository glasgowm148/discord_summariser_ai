# Configuration

This directory contains configuration files for the chat summariser:

- `.env`: Environment variables for API keys, tokens, and other configuration
  ```
  # Discord Configuration
  DISCORD_TOKEN=your_token_here
  DISCORD_SERVER_ID=your_server_id_here
  DISCORD_WEBHOOK_URL=your_webhook_url_here
  DISCORD_WEBHOOK_URL_CHINESE=your_chinese_webhook_here
  # ... other webhook URLs ...

  # Twitter Configuration
  TWITTER_CONSUMER_KEY=your_key_here
  TWITTER_CONSUMER_SECRET=your_secret_here
  TWITTER_ACCESS_TOKEN=your_token_here
  TWITTER_ACCESS_TOKEN_SECRET=your_token_secret_here

  # OpenAI Configuration
  OPENAI_API_KEY=your_api_key_here
  ```

Copy `.env.example` to `.env` and fill in your values.
