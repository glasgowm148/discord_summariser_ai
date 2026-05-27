# Exports

Export scripts wrap DiscordChatExporter and keep generated files out of root.

## Directory Shape

```text
output/YYYY-MM-DD/
  export-<server>_<date-range>_<time>_<days>/
    json_cleaned.json
    json_cleaned_<days>d.csv
    error_log.txt
  historical/
    channel_<channel_id>.csv
    development_<channel_id>.csv
  guild/
    last_week_export/
  logs/
```

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/export_chat.sh` | Interactive full-guild export. |
| `scripts/export.sh` | Thin wrapper for Python interactive export wizard. |
| `scripts/export_wizard.py` | Interactive channel export wizard with guild/channel/timeframe/format menus. |
| `scripts/export_server.sh` | Interactive full-server export variant. |
| `scripts/export_channel.sh` | Channel export by ID and day count. |
| `scripts/export_dev_history.sh` | One-year development channel export. |
| `scripts/export_historical.sh` | Legacy wrapper around `scripts/export_chat.sh`. |
| `scripts/export_and_extract.sh` | Guild export plus question extraction. |
| `scripts/clean_export.py` | Shared JSON-cleaning CLI used by export scripts. |

## Required Environment

All export scripts read `config/.env` and require:

```bash
DISCORD_TOKEN=...
DISCORD_SERVER_ID=...
```

Scripts fail before export if these are missing.

## Cleaning Step

Most export scripts run `JsonCleanerService` after export:

1. Find JSON files in export folder.
2. Drop excluded channels/categories.
3. Drop short messages, forwarded content, IFTTT noise, and summariser messages.
4. Save compact JSON as `json_cleaned.json`.
5. Save CSV as `json_cleaned_<days>d.csv`.

`CsvLoaderService` later searches recursively under `output/` for newest `json_cleaned_*d.csv`.

Manual cleaning:

```bash
python scripts/clean_export.py output/YYYY-MM-DD/export-...
```

Historical output plus cleanup:

```bash
python scripts/clean_export.py output/YYYY-MM-DD/export-... \
  --historical-output output/YYYY-MM-DD/historical/channel_123.csv \
  --cleanup-export-dir
```

## Export Wizard

Use the menu-driven exporter when you want one channel and explicit output path:

```bash
bash scripts/export.sh
```

Defaults:

- guild: `DISCORD_SERVER_ID` from `config/.env`;
- channel: development;
- timeframe: 1 week;
- format: Json;
- output: `output/YYYY-MM-DD/manual-export/<channel>-<id>-<timeframe>-<time>.<format>`.

Set a custom DiscordChatExporter binary path:

```bash
DISCORDCHATEXPORTER_PATH=/path/to/DiscordChatExporter.Cli bash scripts/export.sh
```
