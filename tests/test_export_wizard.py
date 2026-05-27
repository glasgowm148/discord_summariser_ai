import unittest
from pathlib import Path

from config.app_config import AppConfig
from scripts.export_wizard import ExportSelection, build_command, timeframe_after_date


class TestExportWizard(unittest.TestCase):
    def test_all_time_has_no_after_arg(self):
        config = AppConfig(
            project_root=Path("."),
            config_dir=Path("config"),
            output_dir=Path("output"),
            env_path=Path("config/.env"),
            openai_api_key="key",
            discord_server_id="guild",
            discord_token="token",
            discord_exporter_path=Path("exporter"),
        )
        selection = ExportSelection(
            guild_id="guild",
            channel_name="development",
            channel_id="123",
            timeframe="all time",
            export_format="Json",
            after_date="",
            output_path=Path("out.json"),
        )

        command = build_command(config, selection)

        self.assertNotIn("--after", command)
        self.assertEqual(command[-2:], ["-o", "out.json"])

    def test_one_week_has_after_date(self):
        self.assertRegex(timeframe_after_date("1 week"), r"^\d{4}-\d{2}-\d{2}$")
