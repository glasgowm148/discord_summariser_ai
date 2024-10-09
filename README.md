# Dev Summary to Discord Bot

This script is designed to summarize development-related discussions from the Ergo Discord server and post a weekly summary to a specific channel via a Discord webhook. The script processes a chat log exported from Discord, extracts important messages, generates a concise summary using OpenAI's GPT, and posts it to Discord. The tool is currently customized for use with Ergo's Discord server, but it can be adapted to other communities.

## Features
- Extracts messages from an exported Discord chat log (in CSV format).
- Summarizes key points from development updates using OpenAI's API.
- Prioritizes messages from core contributors and highlights specific updates.
- Posts the summarized output to a Discord channel via a webhook.

## Setup

### Prerequisites
- Python 3.x
- OpenAI API key
- Discord Bot key
- Discord webhook URL
- Environment configuration file (`.env`) with necessary variables
- [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) installed to export the chats. 


### Installation
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```
2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Create a `.env` file** in the root directory with the following variables:
   ```env
   OPENAI_API_KEY=<your_openai_api_key>
   DISCORD_WEBHOOK_URL=<your_discord_webhook_url>
   EXPORT_DIR=./output  # Directory where the CSV files are saved
   DISCORD_SERVER_ID=<your_discord_server_id>
   SUMMARY_PROMPT="You are tasked with summarizing the following discussions..."
   PRIORITY_AUTHORS="user1,user2"
   ```
   The `SUMMARY_PROMPT` can be adjusted based on how you want the summary to be generated.

4. **Export Discord chat logs** in CSV format and save them in the directory specified by `EXPORT_DIR`. The CSV should have columns such as `author`, `msg`, `msg_id`, `channel_id`, and `timestamp`.

### Running the Script(s)

#### Discord -> Twitter Auto-post

```
./export_chat.sh 1d channel
python3 tweet.py
```

#### Discord -> Newsletter

1. **Execute the script**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
2. The script will:
   - Load the latest CSV file from the specified directory.
   - Extract messages from the development discussion, prioritizing specific core contributors and significant messages after a development update call.
   - Generate a summary using OpenAI's GPT model.
   - Post the summary to Discord using the specified webhook URL.

## Customization
This script is currently set up specifically for Ergo's Discord server. If you want to use it for another community or server, you'll need to customize the following parts:

1. **Environment Variables**: Rename `.sample_env` to `.env` file to reflect your Discord server's details (e.g., webhook URL, server ID, priority authors).

2. **Priority Authors**: The script uses `PRIORITY_AUTHORS` to give emphasis to core contributors. You can adjust this list in the `.env` file to match your community's needs.

3. **SUMMARY_PROMPT**: Customize the `SUMMARY_PROMPT` in the `.env` to tweak the summarization approach to suit the type of content generated in your server.

4. **Message Parsing**: The message identification logic (`"share your updates" in row['msg'].lower()`) may need to be adjusted to fit the format of your development updates or community events.

## Automation

```
chmod +x enable_service.sh
```

## Contributing
Feel free to fork the repository and create pull requests if you want to add new features, fix bugs, or make the script more generalized. Contributions are welcome!

## License
This project is open source under the MIT License. See the `LICENSE` file for more information.

