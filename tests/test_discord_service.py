import unittest
from unittest.mock import patch

try:
    from services.social_media.discord_service import DiscordService
except ImportError as exc:
    DiscordService = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(DiscordService is None, f"Optional dependency missing: {IMPORT_ERROR}")
class TestDiscordService(unittest.TestCase):
    @patch("services.social_media.discord_service.load_dotenv")
    @patch("services.social_media.discord_service.Path.exists", return_value=True)
    def test_split_into_chunks_preserves_limit(self, *_):
        service = DiscordService()

        chunks = service._split_into_chunks("a" * 5 + "\n" + "b" * 5, 6)

        self.assertEqual(chunks, ["aaaaa", "bbbbb"])
