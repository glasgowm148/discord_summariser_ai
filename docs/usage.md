# Usage

## Normal Workflow

1. Configure `config/.env`.
2. Export Discord data.
3. Let export script clean JSON into CSV.
4. Run summariser.
5. Review generated bullets and summaries.
6. Confirm any social posting prompts.

## Export Whole Server

```bash
bash scripts/export_chat.sh
```

The script asks for day count, exports guild JSON, cleans it, and saves outputs under `output/YYYY-MM-DD/export-.../`.

## Export One Channel

```bash
bash scripts/export_channel.sh 669989266478202917 30
```

Arguments:

| Position | Meaning | Default |
| --- | --- | --- |
| 1 | Discord channel ID | development channel |
| 2 | days back | `365` |

Cleaned CSV also lands in `output/YYYY-MM-DD/historical/`.

## Generate Summary

```bash
python scripts/summarise.py
```

The script finds latest `json_cleaned_*d.csv` under `output/`, generates update bullets with OpenAI, builds Discord/Reddit summaries, and asks before posting.

## AMA Question Extraction

```bash
bash scripts/export_and_extract.sh
```

Writes:

```text
output/YYYY-MM-DD/questions_for_ama.txt
```

## Historical Knowledge Build

```bash
python scripts/build_knowledge_base.py
```

Exports development history, reads `output/*/historical/*.csv`, summarises periods, and updates project knowledge in `output/projects.db`.
