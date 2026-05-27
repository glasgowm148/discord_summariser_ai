# Troubleshooting

## `config/.env file not found`

```bash
cp config/.env.example config/.env
```

Then fill required values.

## Missing Environment Variables

`scripts/summarise.py` validates variables in `config/settings.py`. Add missing keys to `config/.env`, or loosen validation for partial workflows.

Export scripts require:

```bash
DISCORD_TOKEN=...
DISCORD_SERVER_ID=...
```

## DiscordChatExporter Not Found

Scripts expect:

```text
DiscordChatExporter/DiscordChatExporter-linux/mac/DiscordChatExporter.Cli.osx-arm64/DiscordChatExporter.Cli
```

Update `EXPORTER` or `EXPORTER_PATH` in the relevant script if your binary differs.

## No CSV Files Found

Run export first:

```bash
bash scripts/export_chat.sh
```

Expected:

```text
output/YYYY-MM-DD/export-.../json_cleaned_<days>d.csv
```

`CsvLoaderService` searches recursively under `output/`.

## OpenAI Errors

Check:

- `OPENAI_API_KEY` in `config/.env`;
- dependency versions;
- `output/YYYY-MM-DD/logs/summary_generator.log`.

## Reddit Posting Fails

Check:

- `REDDIT_USERNAME`, `REDDIT_PASSWORD`, `REDDIT_SUBREDDIT`;
- `playwright install chromium`;
- `REDDIT_DEBUG=true` for visible browser;
- logs under `output/YYYY-MM-DD/logs/`.

## Root Directory Gets Messy

Expected root files:

```text
README.md
pyproject.toml
requirements.txt
.gitignore
```

Exports/logs belong in `output/YYYY-MM-DD/`. Local secrets belong in `config/.env`.
