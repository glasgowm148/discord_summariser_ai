# Project Layout

Root is kept minimal:

```text
README.md
pyproject.toml
requirements.txt
.gitignore
```

## Directories

| Path | Purpose |
| --- | --- |
| `config/` | Settings, `.env.example`, local ignored `.env`, export command notes. |
| `docs/` | Human docs. |
| `helpers/` | Formatters, processors, validators. |
| `models/` | Dataclasses and SQLite-backed project model. |
| `scripts/` | CLI entrypoints and export/maintenance scripts. |
| `services/` | Core services and social media integrations. |
| `tests/` | Lightweight tests. |
| `utils/` | Prompts and logging config. |
| `output/` | Generated exports, cleaned CSVs, logs, SQLite state, summary history. Ignored. |
| `guild/` | Imported Discord exports. Ignored. |
| `DiscordChatExporter/` | Local exporter binary. Ignored. |

## Main Entry Points

| File | Purpose |
| --- | --- |
| `scripts/summarise.py` | Main interactive summary workflow. |
| `scripts/summarise2.py` | Older experimental rich/inquirer CLI. |
| `scripts/export_chat.sh` | Full guild export. |
| `scripts/export_channel.sh` | Single channel export. |
| `scripts/export_and_extract.sh` | Export and extract questions. |
| `scripts/build_knowledge_base.py` | Build project database from historical CSVs. |
