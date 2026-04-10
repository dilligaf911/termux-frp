from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv_if_present(path: Path = Path('.env')) -> None:
    if not path.exists() or not path.is_file():
        return

    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv_if_present()


def _parse_chat_ids(raw: str) -> set[int]:
    result: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        result.add(int(part))
    return result


def _parse_csv(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


def _parse_safe_commands(raw_json: str) -> dict[str, list[str]]:
    data = json.loads(raw_json)
    if not isinstance(data, dict):
        raise RuntimeError("SAFE_COMMANDS_JSON must be a JSON object")

    parsed: dict[str, list[str]] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not key.strip():
            raise RuntimeError("SAFE_COMMANDS_JSON keys must be non-empty strings")
        if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
            raise RuntimeError("SAFE_COMMANDS_JSON values must be non-empty arrays of strings")
        parsed[key.strip().lower()] = value
    return parsed


DEFAULT_SAFE_COMMANDS: dict[str, list[str]] = {
    "status": ["systemctl", "is-system-running"],
    "uptime": ["uptime"],
    "disk": ["df", "-h"],
    "memory": ["free", "-h"],
    "who": ["who"],
    "top": ["top", "-b", "-d", "1"],
}


@dataclass(slots=True)
class Settings:
    bot_token: str
    allowed_chat_ids: set[int]
    upload_dir: Path = Path("./data/uploads")
    download_dir: Path = Path("./data/downloads")
    max_upload_bytes: int = 5 * 1024 * 1024
    allowed_upload_extensions: set[str] = field(default_factory=lambda: {".txt", ".log", ".json", ".csv"})
    allowed_services: set[str] = field(default_factory=set)
    safe_commands: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_SAFE_COMMANDS))

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("BOT_TOKEN is required")

        raw_chat_ids = os.getenv("ALLOWED_CHAT_IDS", "").strip()
        if not raw_chat_ids:
            raise RuntimeError("ALLOWED_CHAT_IDS is required")

        upload_dir = Path(os.getenv("UPLOAD_DIR", "./data/uploads")).resolve()
        download_dir = Path(os.getenv("DOWNLOAD_DIR", "./data/downloads")).resolve()

        safe_commands_json = os.getenv("SAFE_COMMANDS_JSON", "").strip()
        safe_commands = dict(DEFAULT_SAFE_COMMANDS)
        if safe_commands_json:
            safe_commands = _parse_safe_commands(safe_commands_json)

        settings = cls(
            bot_token=token,
            allowed_chat_ids=_parse_chat_ids(raw_chat_ids),
            upload_dir=upload_dir,
            download_dir=download_dir,
            max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024))),
            allowed_upload_extensions=_parse_csv(os.getenv("ALLOWED_UPLOAD_EXTENSIONS", ".txt,.log,.json,.csv")),
            allowed_services=_parse_csv(os.getenv("ALLOWED_SERVICES", "")),
            safe_commands=safe_commands,
        )
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        settings.download_dir.mkdir(parents=True, exist_ok=True)
        return settings
