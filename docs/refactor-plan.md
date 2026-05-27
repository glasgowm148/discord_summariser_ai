# Refactor Plan

## Fixed In Current Pass

- Main summariser now requires only `OPENAI_API_KEY` and `DISCORD_SERVER_ID`.
- Discord, Reddit, Twitter/X, and Meta services are lazy-loaded only when user chooses posting.
- HackMD service is lazy-loaded only when `post_to_hackmd=True`.
- Reddit posting coroutine is now awaited instead of treated as truthy sync result.
- Discord summary now uses curated top updates while Reddit keeps full update set.
- Noisy pipeline `print()` diagnostics in core processors moved to logger.
- Repeated shell-script JSON-cleaning blocks moved to `scripts/clean_export.py`.

## Biggest Remaining Problems

| Area | Problem | Recommended Fix |
| --- | --- | --- |
| `scripts/summarise.py` | Interactive orchestration, service lifecycle, and posting prompts all in one class. | Split into CLI layer, `SummaryWorkflow`, and posting adapters. |
| `services/summary_generator.py` | Does conversion, chunking, bullet generation, curation, optional HackMD, and finalisation. | Split curation/finalisation from generation; return structured result object. |
| `helpers/processors/bullet_processor.py` | Retry loop, validation, link repair, and dedupe coupled tightly. | Create `UpdateGenerationResult`; isolate retry policy. |
| Social services | Use `print()`, direct `requests`, weak credential validation, mixed sync/async APIs. | Add shared `HttpClient` wrapper, logger use, explicit `validate_credentials()`. |
| Export scripts | Shell still handles date math and exporter paths. | Move export orchestration into Python CLI; keep shell wrappers thin. |
| Config | Required env is scattered across scripts/services. | Central config object with per-feature validation. |
| Tests | Only one pure unit test. | Add tests for chunking, CSV discovery, JSON cleaning, formatting, and lazy service init. |
| Legacy code | `scripts/summarise2.py`, `scripts/chat_combined.py`, and bot scripts are experimental. | Mark as legacy or move under `scripts/legacy/` after confirming use. |

## Suggested Order

1. Add tests around current behavior before deeper rewrites.
2. Introduce `AppConfig` and central path helpers.
3. Convert export scripts to Python subcommands.
4. Split summary pipeline into small pure components.
5. Standardize logging and remove remaining `print()` from services.
6. Normalize async boundaries: either async posting all the way or sync wrappers.
7. Delete or quarantine legacy scripts.

## Quick Wins

- Add `--no-post`, `--discord`, `--reddit`, `--twitter`, `--meta` flags to `scripts/summarise.py`.
- Add `--input-csv` to summariser for deterministic runs.
- Add `--dry-run` to social posting services.
- Add sample fixture JSON under `tests/fixtures/`.
- Add CI command: `python -m unittest discover -s tests -q`.
