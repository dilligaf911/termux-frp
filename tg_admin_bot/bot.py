from __future__ import annotations

import logging
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .commands import run_safe_command, service_logs, service_restart
from .config import Settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("tg-admin-bot")


def _is_authorized(update: Update, settings: Settings) -> bool:
    chat = update.effective_chat
    if chat is None:
        return False
    return chat.id in settings.allowed_chat_ids


async def _guard(update: Update, settings: Settings) -> bool:
    if _is_authorized(update, settings):
        return True
    if update.effective_message:
        await update.effective_message.reply_text("Access denied: your chat_id is not allowed.")
    logger.warning("Unauthorized access attempt from chat_id=%s", update.effective_chat.id if update.effective_chat else "unknown")
    return False


def _format_result(title: str, output: str) -> str:
    if not output:
        output = "(empty output)"
    if len(output) > 3500:
        output = output[:3500] + "\n...<truncated>"
    return f"{title}\n\n{output}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await _guard(update, settings):
        return

    safe_commands = ", ".join(sorted(settings.safe_commands.keys()))
    await update.message.reply_text(
        "Safe Admin Bot MVP\n"
        f"Commands: {safe_commands}\n"
        "/safe <command>\n"
        "/logs <service> [lines]\n"
        "/restart <service>\n"
        "/get <filename> (from download dir)\n"
        "Send a file to upload (allowed extensions only)."
    )


async def safe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await _guard(update, settings):
        return

    if not context.args:
        await update.message.reply_text("Usage: /safe <command>")
        return

    command_name = context.args[0].strip().lower()
    try:
        result = await run_safe_command(command_name, settings.safe_commands)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return

    status = f"command: {result.command}\nexit_code: {result.returncode}\ntimeout: {result.timed_out}"
    body = result.stdout or result.stderr
    await update.message.reply_text(_format_result(status, body))


async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await _guard(update, settings):
        return

    if not context.args:
        await update.message.reply_text("Usage: /logs <service> [lines]")
        return

    service = context.args[0].strip()
    if settings.allowed_services and service not in settings.allowed_services:
        await update.message.reply_text("Service is not in ALLOWED_SERVICES")
        return

    lines = 80
    if len(context.args) > 1:
        try:
            lines = int(context.args[1])
        except ValueError:
            await update.message.reply_text("lines must be integer")
            return

    result = await service_logs(service, lines)
    status = f"command: {result.command}\nexit_code: {result.returncode}\ntimeout: {result.timed_out}"
    body = result.stdout or result.stderr
    await update.message.reply_text(_format_result(status, body))


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await _guard(update, settings):
        return

    if not context.args:
        await update.message.reply_text("Usage: /restart <service>")
        return

    service = context.args[0].strip()
    if settings.allowed_services and service not in settings.allowed_services:
        await update.message.reply_text("Service is not in ALLOWED_SERVICES")
        return

    result = await service_restart(service)
    status = f"command: {result.command}\nexit_code: {result.returncode}\ntimeout: {result.timed_out}"
    body = result.stdout or result.stderr or "Service restart request sent."
    await update.message.reply_text(_format_result(status, body))


async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await _guard(update, settings):
        return

    message = update.effective_message
    if message is None or message.document is None:
        return

    doc = message.document
    if doc.file_size and doc.file_size > settings.max_upload_bytes:
        await message.reply_text(f"File too large. Max bytes: {settings.max_upload_bytes}")
        return

    filename = Path(doc.file_name or "uploaded.bin").name
    ext = Path(filename).suffix.lower()
    if settings.allowed_upload_extensions and ext not in settings.allowed_upload_extensions:
        await message.reply_text(f"Extension not allowed: {ext}")
        return

    target = settings.upload_dir / filename
    tg_file = await context.bot.get_file(doc.file_id)
    await tg_file.download_to_drive(custom_path=str(target))
    await message.reply_text(f"Uploaded to: {target}")


async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not await _guard(update, settings):
        return

    if not context.args:
        await update.message.reply_text("Usage: /get <filename>")
        return

    filename = Path(context.args[0]).name
    path = (settings.download_dir / filename).resolve()
    if not path.exists() or not path.is_file():
        await update.message.reply_text("File not found")
        return

    if path.parent != settings.download_dir:
        await update.message.reply_text("Invalid file path")
        return

    with path.open("rb") as f:
        await update.message.reply_document(document=f, filename=filename)


def build_app(settings: Settings) -> Application:
    app = Application.builder().token(settings.bot_token).build()
    app.bot_data["settings"] = settings

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("safe", safe))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("get", get_file))
    app.add_handler(MessageHandler(filters.Document.ALL, upload_file))
    return app


def main() -> None:
    settings = Settings.from_env()
    app = build_app(settings)
    logger.info("Starting bot with polling")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
