"""Application configuration loaded from environment and config/.env."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "output"
ENV_PATH = CONFIG_DIR / ".env"


def _load_env_file(path: Path = ENV_PATH) -> None:
    """Load simple KEY=VALUE lines without requiring python-dotenv at import time."""
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class AppConfig:
    """Central config object for core app paths and credentials."""

    project_root: Path
    config_dir: Path
    output_dir: Path
    env_path: Path
    openai_api_key: str
    discord_server_id: str
    discord_token: str = ""
    discord_exporter_path: Path = PROJECT_ROOT / "DiscordChatExporter" / "DiscordChatExporter-linux" / "mac" / "DiscordChatExporter.Cli.osx-arm64" / "DiscordChatExporter.Cli"

    @classmethod
    def load(cls, require_env_file: bool = True) -> "AppConfig":
        if require_env_file and not ENV_PATH.exists():
            raise FileNotFoundError(
                "config/.env file not found. Please copy config/.env.example "
                "to config/.env and fill in your values."
            )

        _load_env_file(ENV_PATH)

        exporter = os.getenv("DISCORDCHATEXPORTER_PATH")
        return cls(
            project_root=PROJECT_ROOT,
            config_dir=CONFIG_DIR,
            output_dir=OUTPUT_DIR,
            env_path=ENV_PATH,
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            discord_server_id=os.getenv("DISCORD_SERVER_ID", ""),
            discord_token=os.getenv("DISCORD_TOKEN", ""),
            discord_exporter_path=Path(exporter) if exporter else cls.discord_exporter_path,
        )

    def require(self, keys: Iterable[str]) -> None:
        missing = [key for key in keys if not getattr(self, key)]
        if missing:
            raise ValueError(f"Missing required config values: {', '.join(missing)}")

    def require_core_summary(self) -> None:
        self.require(["openai_api_key", "discord_server_id"])

    def require_export(self) -> None:
        self.require(["discord_token", "discord_server_id"])
        if not self.discord_exporter_path.exists():
            raise FileNotFoundError(f"DiscordChatExporter not found: {self.discord_exporter_path}")
