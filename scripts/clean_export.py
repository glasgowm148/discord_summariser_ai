#!/usr/bin/env python3
"""Clean a DiscordChatExporter JSON export directory."""

import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def clean_export(
    export_dir: Path,
    historical_output: Path | None = None,
    cleanup_export_dir: bool = False,
) -> None:
    """Clean export JSON, optionally copy CSV to historical output and remove export dir."""
    from services.json_cleaner import JsonCleanerService

    cleaner = JsonCleanerService()
    json_files, search_dir = cleaner.get_json_files(str(export_dir))
    all_cleaned_data = []
    errors = []

    for json_file in json_files:
        print(f"Processing JSON file: {json_file}")
        try:
            with open(json_file) as f:
                data = __import__("json").load(f)
            all_cleaned_data.extend(cleaner.clean_chatlog_data(data))
        except Exception as exc:
            message = f"Error processing file {json_file}: {exc}"
            print(message)
            errors.append(message)

    if all_cleaned_data:
        cleaner.save_json(all_cleaned_data, search_dir)
        days_covered = cleaner.get_days_covered(all_cleaned_data)
        cleaner.save_csv(all_cleaned_data, search_dir, days_covered)
        cleaner.print_stats(all_cleaned_data)

    if errors:
        error_path = Path(search_dir) / "error_log.txt"
        error_path.write_text("\n".join(errors))

    if historical_output:
        csv_files = list(Path(search_dir).rglob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV file found in {search_dir}")
        historical_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(csv_files[0]), historical_output)
        print(f"Saved historical CSV to {historical_output}")

    if cleanup_export_dir:
        shutil.rmtree(export_dir)
        print(f"Removed export directory {export_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_dir", type=Path)
    parser.add_argument("--historical-output", type=Path)
    parser.add_argument("--cleanup-export-dir", action="store_true")
    args = parser.parse_args()

    clean_export(args.export_dir, args.historical_output, args.cleanup_export_dir)


if __name__ == "__main__":
    main()
