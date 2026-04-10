import asyncio
import unittest

from tg_admin_bot.commands import run_safe_command


class CommandTestCase(unittest.TestCase):
    def test_run_safe_command_unknown_raises(self) -> None:
        async def _run() -> None:
            with self.assertRaises(ValueError):
                await run_safe_command("unknown", {"uptime": ["uptime"]})

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
