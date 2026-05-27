# Refactor Plan

## Fixed In Current Pass

- Main summariser now requires only `OPENAI_API_KEY` and `DISCORD_SERVER_ID`.
- Discord, Reddit, Twitter/X, and Meta services are lazy-loaded only when user chooses posting.
- HackMD service is lazy-loaded only when `post_to_hackmd=True`.
- Reddit posting coroutine is now awaited instead of treated as truthy sync result.
- Discord summary now uses curated top updates while Reddit keeps full update set.
- Noisy pipeline `print()` diagnostics in core processors moved to logger.
- Repeated shell-script JSON-cleaning blocks moved to `scripts/clean_export.py`.
- Added central `AppConfig` with per-feature validation.
- Split CLI from summary workflow: `scripts/summarise.py` now delegates to `services/summary_workflow.py`.
- Added `services/posting_adapters.py` for lazy social integrations.
- Added `services/http_client.py` and moved Discord/Twitter services toward logger + shared HTTP wrapper.
- Replaced shell-heavy export wizard with `scripts/export_wizard.py`; `scripts/export.sh` is now a thin wrapper.
- Added tests for config loading, export command building, and Discord chunking.
- Moved older CLI experiments under `scripts/legacy/`.
- Added `SummaryResult` from `SummaryGenerator.generate_result()` while preserving tuple API.
- Added `UpdateGenerationResult` from `BulletProcessor.process_chunks_result()` while preserving list API.

## Biggest Remaining Problems

| Area | Problem | Recommended Fix |
| --- | --- | --- |
| `services/summary_generator.py` | Still owns several pipeline stages. | Split curation/finalisation into separate collaborators once result object is adopted everywhere. |
| `helpers/processors/bullet_processor.py` | Retry loop, validation, link repair, and dedupe remain in one class. | Isolate retry policy next; `UpdateGenerationResult` now gives safer boundary. |
| Social services | Discord/Twitter improved, but Reddit/Meta still need shared HTTP/logging cleanup and async boundary review. | Finish `HttpClient` migration and explicit `validate_credentials()` methods. |
| Shell exports | Existing legacy shell export scripts remain alongside Python wizard. | Keep as compatibility wrappers or fold into Python subcommands. |
| Tests | Coverage improved but still thin. | Add fixture-based JSON cleaning, CSV discovery, formatting, and lazy service init tests. |

## Suggested Order

1. Add fixture-based tests for core data transforms.
2. Split `SummaryGenerator` result construction from finalisation.
3. Split `BulletProcessor` retry policy from validation/link repair.
4. Finish social service HTTP/logging migration.
5. Fold old export shell scripts into Python subcommands or delete.
6. Review `scripts/legacy/` and delete if no longer useful.

## Quick Wins

- Add `--no-post`, `--discord`, `--reddit`, `--twitter`, `--meta` flags to `scripts/summarise.py`.
- Add `--input-csv` to summariser for deterministic runs.
- Add `--dry-run` to social posting services.
- Add sample fixture JSON under `tests/fixtures/`.
- Add CI command: `python -m unittest discover -s tests -q`.
