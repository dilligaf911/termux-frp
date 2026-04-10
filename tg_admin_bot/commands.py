from __future__ import annotations

import asyncio
import shlex
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


async def run_command(command: list[str], timeout_sec: int = 5) -> CommandResult:
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    timed_out = False
    try:
        stdout_raw, stderr_raw = await asyncio.wait_for(process.communicate(), timeout=timeout_sec)
    except TimeoutError:
        timed_out = True
        process.kill()
        stdout_raw, stderr_raw = await process.communicate()

    return CommandResult(
        command=shlex.join(command),
        returncode=process.returncode if process.returncode is not None else 124,
        stdout=stdout_raw.decode("utf-8", errors="replace").strip(),
        stderr=stderr_raw.decode("utf-8", errors="replace").strip(),
        timed_out=timed_out,
    )


async def run_safe_command(name: str, safe_commands: dict[str, list[str]]) -> CommandResult:
    key = name.lower()
    if key not in safe_commands:
        raise ValueError(f"Unknown safe command: {name}")
    timeout = 5 if key in {"top", "htop", "mc"} else 4
    return await run_command(safe_commands[key], timeout_sec=timeout)


async def service_logs(service: str, lines: int = 80) -> CommandResult:
    lines = min(max(lines, 10), 200)
    return await run_command(["journalctl", "-u", service, "-n", str(lines), "--no-pager"], timeout_sec=5)


async def service_restart(service: str) -> CommandResult:
    return await run_command(["systemctl", "restart", service], timeout_sec=5)
