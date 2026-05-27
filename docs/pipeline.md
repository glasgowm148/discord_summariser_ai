# Summarisation Pipeline

## High-Level Flow

```text
DiscordChatExporter JSON
  -> JsonCleanerService
  -> json_cleaned_<days>d.csv
  -> CsvLoaderService
  -> DiscordMessage models
  -> ChunkProcessor
  -> BulletProcessor
  -> SummaryFinalizer
  -> Discord / Reddit / Twitter / Meta outputs
```

## Main Runtime

`scripts/summarise.py`:

1. Loads `config/.env`.
2. Validates required env vars from `config/settings.py`.
3. Creates CSV, OpenAI, Discord, Twitter/X, Reddit, and Meta services.
4. Loads latest cleaned CSV from `output/`.
5. Generates summaries.
6. Shows previews.
7. Asks before posting.

## Core Services

| Component | Role |
| --- | --- |
| `services/csv_loader.py` | Finds newest cleaned CSV and parses day count. |
| `services/json_cleaner.py` | Converts DiscordChatExporter JSON to compact JSON and CSV. |
| `services/summary_generator.py` | Converts rows to message models, chunks messages, generates bullets, builds final summaries. |
| `services/summary_finalizer.py` | Produces platform-specific final text and saves summary history. |
| `services/project_manager.py` | Learns project names/details from summaries into SQLite. |
| `services/service_factory.py` | Builds shared service instances. |

## Helpers

| Component | Role |
| --- | --- |
| `helpers/processors/chunk_processor.py` | Groups `DiscordMessage` objects into prompt-sized chunks. |
| `helpers/processors/bullet_processor.py` | Runs update extraction, validation, link repair, and dedupe. |
| `helpers/processors/update_extractor.py` | Uses OpenAI prompts to extract updates from chunks. |
| `helpers/processors/update_deduplicator.py` | Removes near-duplicate updates. |
| `helpers/processors/discord_link_processor.py` | Builds and fixes Discord message links. |
| `helpers/formatters/*` | Formats final content for Discord/social surfaces. |
| `helpers/validators/*` | Checks generated content quality. |

## Models

- `models/discord_message.py`: message IDs, channel metadata, content, author, timestamp, link generation.
- `models/bullet_point.py`: generated update metadata.
- `models/project.py`: SQLite-backed project knowledge.

## OpenAI Use

OpenAI is used for update extraction, summary finalisation, social rewrites, and optional Meta theme/image prompt work.
