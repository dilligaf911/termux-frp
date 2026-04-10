import os
import tempfile
import unittest
from pathlib import Path

from tg_admin_bot.config import Settings


class SettingsTestCase(unittest.TestCase):
    def test_from_env_parses_safe_commands_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["BOT_TOKEN"] = "token"
            os.environ["ALLOWED_CHAT_IDS"] = "1,2"
            os.environ["UPLOAD_DIR"] = str(Path(tmpdir) / "up")
            os.environ["DOWNLOAD_DIR"] = str(Path(tmpdir) / "down")
            os.environ["SAFE_COMMANDS_JSON"] = '{"uptime":["uptime"],"disk":["df","-h"]}'

            settings = Settings.from_env()

            self.assertEqual(settings.allowed_chat_ids, {1, 2})
            self.assertIn("uptime", settings.safe_commands)
            self.assertEqual(settings.safe_commands["disk"], ["df", "-h"])
            self.assertTrue(settings.upload_dir.exists())
            self.assertTrue(settings.download_dir.exists())


if __name__ == "__main__":
    unittest.main()
