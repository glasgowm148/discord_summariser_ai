# Setup

## Python Environment

Use Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

Fallback install:

```bash
pip install -r requirements.txt
```

## Environment File

```bash
cp config/.env.example config/.env
```

Fill only values needed for your workflow. `config/.env` is ignored by git.

Minimum for export and summary:

```bash
DISCORD_TOKEN=your_discord_export_token
DISCORD_SERVER_ID=your_discord_server_id
OPENAI_API_KEY=your_openai_api_key
```

Posting workflows need extra keys for Discord webhooks, Twitter/X, Reddit, HackMD, or Meta. See `config/.env.example`.

## DiscordChatExporter

Scripts expect:

```text
DiscordChatExporter/DiscordChatExporter-linux/mac/DiscordChatExporter.Cli.osx-arm64/DiscordChatExporter.Cli
```

If binary differs, update `EXPORTER` / `EXPORTER_PATH` in the script you use.

## Checks

```bash
python -m compileall -q config helpers models services scripts tests utils
python -m unittest discover -s tests -q
python -m pytest
ruff check .
```
