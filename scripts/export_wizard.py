#!/usr/bin/env python3
"""Interactive DiscordChatExporter wizard."""

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.app_config import AppConfig


CHANNELS = [
    ("development", "669989266478202917"),
    ("dev-support", "840313005064585246"),
    ("ergoscript-support", "849659724495323206"),
    ("support", "670288337747312646"),
    ("ask-anything", "908347206988365864"),
    ("mining", "668913770059268125"),
    ("dev-tooling", "1073483623459725322"),
    ("rosen", "964131671609860126"),
    ("sigmausd", "802828538197573682"),
]
TIMEFRAMES = ["1 week", "1 month", "since start of year", "1 year", "all time"]
FORMATS = ["Json", "PlainText", "Html", "Csv"]


@dataclass(frozen=True)
class ExportSelection:
    guild_id: str
    channel_name: str
    channel_id: str
    timeframe: str
    export_format: str
    after_date: str
    output_path: Path


def slugify(value: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", value.lower()))


def choose(title: str, options: list[str], default: int = 1) -> str:
    print(f"\n{title}")
    for idx, option in enumerate(options, 1):
        marker = "*" if idx == default else " "
        print(f"  {marker} {idx}) {option}")

    raw = input(f"Select [{default}]: ").strip() or str(default)
    if not raw.isdigit() or not 1 <= int(raw) <= len(options):
        raise ValueError(f"Invalid selection: {raw}")
    return options[int(raw) - 1]


def timeframe_after_date(timeframe: str) -> str:
    now = datetime.now(timezone.utc)
    if timeframe == "1 week":
        return (now - timedelta(days=7)).date().isoformat()
    if timeframe == "1 month":
        return (now - timedelta(days=31)).date().isoformat()
    if timeframe == "since start of year":
        return f"{now.year}-01-01"
    if timeframe == "1 year":
        return (now - timedelta(days=365)).date().isoformat()
    return ""


def build_selection(config: AppConfig) -> ExportSelection:
    print("Discord export wizard")
    print(f"Using config: {config.env_path.relative_to(config.project_root)}")
    print(f"\nConfigured guild ID: {config.discord_server_id}")
    guild_input = input("Press Enter to use this guild, or type another guild ID: ").strip()
    guild_id = guild_input or config.discord_server_id

    channel_options = [f"{name} | {channel_id}" for name, channel_id in CHANNELS]
    channel_options.append("custom channel ID")
    channel_label = choose("Channel", channel_options, default=1)
    if channel_label == "custom channel ID":
        channel_name = "custom"
        channel_id = input("Channel ID: ").strip()
        if not channel_id:
            raise ValueError("Channel ID required")
    else:
        channel_name, channel_id = channel_label.split(" | ", 1)

    timeframe = choose("Timeframe", TIMEFRAMES, default=1)
    export_format = choose("Export format", FORMATS, default=1)

    export_date = datetime.now(timezone.utc).date().isoformat()
    timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
    output_dir = config.output_dir / export_date / "manual-export"
    output_path = output_dir / (
        f"guild-{slugify(guild_id)}-"
        f"{slugify(channel_name)}-{channel_id}-"
        f"{slugify(timeframe)}-{timestamp}.{slugify(export_format)}"
    )

    return ExportSelection(
        guild_id=guild_id,
        channel_name=channel_name,
        channel_id=channel_id,
        timeframe=timeframe,
        export_format=export_format,
        after_date=timeframe_after_date(timeframe),
        output_path=output_path,
    )


def build_command(config: AppConfig, selection: ExportSelection) -> list[str]:
    command = [
        str(config.discord_exporter_path),
        "export",
        "--channel",
        selection.channel_id,
        "--token",
        config.discord_token,
    ]
    if selection.after_date:
        command.extend(["--after", selection.after_date])
    command.extend([
        "--format",
        selection.export_format,
        "-o",
        str(selection.output_path),
    ])
    return command


def print_plan(selection: ExportSelection) -> None:
    print("\nExport plan")
    print(f"  Guild:     {selection.guild_id}")
    print(f"  Channel:   {selection.channel_name} ({selection.channel_id})")
    print(f"  Timeframe: {selection.timeframe}")
    print(f"  Format:    {selection.export_format}")
    print(f"  Output:    {selection.output_path}")


def main() -> None:
    if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
        print(__doc__)
        print("\nRun without arguments for interactive export wizard.")
        return

    config = AppConfig.load()
    config.require_export()
    selection = build_selection(config)
    print_plan(selection)

    confirm = input("\nRun export? [Y/n]: ").strip() or "Y"
    if confirm.lower() != "y":
        print("Cancelled.")
        return

    selection.output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(build_command(config, selection), check=True)
    print("\nExported file:")
    print(selection.output_path)


if __name__ == "__main__":
    main()
