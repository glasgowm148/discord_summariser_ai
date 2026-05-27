# Discord Summariser AI

Python tools for turning Discord exports into Ergo community summaries and optional social posts.

## Docs

- [Docs index](docs/index.md)
- [Setup](docs/setup.md)
- [Usage](docs/usage.md)
- [Exports](docs/exports.md)
- [Summarisation pipeline](docs/pipeline.md)
- [Social posting](docs/social-posting.md)
- [Project layout](docs/project-layout.md)
- [Troubleshooting](docs/troubleshooting.md)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
cp config/.env.example config/.env
```

Fill `config/.env`, export Discord data, then run:

```bash
bash scripts/export.sh
python scripts/summarise.py
```

`scripts/summarise.py` loads newest cleaned CSV from `output/`, generates update bullets with OpenAI, previews summaries, then asks before posting to Discord, Reddit, Twitter/X, or Meta.

## Checks

```bash
python -m compileall -q config helpers models services scripts tests utils
python -m unittest discover -s tests -q
python -m pytest
ruff check .
```

## Project Shape

Root stays minimal. Code lives in `scripts/`, `services/`, `helpers/`, `models/`, and `utils/`. Generated exports/logs live under `output/YYYY-MM-DD/` and are ignored by git.
