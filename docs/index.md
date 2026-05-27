# Documentation

Discord Summariser AI turns DiscordChatExporter output into cleaned CSV files, AI-generated update bullets, final summaries, and optional social posts.

## Read These First

- [Setup](setup.md): environment, dependencies, `.env`, and checks.
- [Usage](usage.md): normal export-to-summary workflow.
- [Exports](exports.md): how scripts write files under `output/YYYY-MM-DD/`.
- [Pipeline](pipeline.md): how JSON becomes summaries.
- [Social Posting](social-posting.md): Discord, Reddit, Twitter/X, Meta, and bot flows.
- [Project Layout](project-layout.md): where code, data, docs, logs, and config live.
- [Troubleshooting](troubleshooting.md): common failures and fixes.
- [Refactor Plan](refactor-plan.md): current cleanup status and next refactor slices.

## Current Entry Points

| Task | Command |
| --- | --- |
| Main summariser | `python scripts/summarise.py` |
| Export wizard | `bash scripts/export.sh` |
| Export whole server | `bash scripts/export_chat.sh` |
| Export one channel | `bash scripts/export_channel.sh <channel_id> <days>` |
| Export development history | `bash scripts/export_dev_history.sh` |
| Extract AMA questions | `bash scripts/export_and_extract.sh` |
| Build historical project knowledge | `python scripts/build_knowledge_base.py` |

## Output Convention

```text
output/YYYY-MM-DD/
  export-.../
  guild/
  historical/
  logs/
  questions_for_ama.txt
```

Do not commit exports, logs, `.env`, local caches, or DiscordChatExporter binaries.
