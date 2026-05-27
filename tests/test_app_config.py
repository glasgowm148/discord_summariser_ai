import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config.app_config import AppConfig, _load_env_file


class TestAppConfig(unittest.TestCase):
    def test_load_env_file_does_not_override_existing_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("OPENAI_API_KEY=file-value\nDISCORD_SERVER_ID=server\n")

            with patch.dict(os.environ, {"OPENAI_API_KEY": "existing"}, clear=True):
                _load_env_file(env_file)

                self.assertEqual(os.environ["OPENAI_API_KEY"], "existing")
                self.assertEqual(os.environ["DISCORD_SERVER_ID"], "server")

    def test_require_reports_missing_fields(self):
        config = AppConfig(
            project_root=Path("."),
            config_dir=Path("config"),
            output_dir=Path("output"),
            env_path=Path("config/.env"),
            openai_api_key="",
            discord_server_id="server",
        )

        with self.assertRaisesRegex(ValueError, "openai_api_key"):
            config.require_core_summary()
