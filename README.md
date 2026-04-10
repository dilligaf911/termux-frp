# Safe Telegram Admin Bot MVP

Безопасный MVP Telegram-бота для администрирования **без произвольного shell exec**.

## Что умеет

- Polling через Bot API (`python-telegram-bot`).
- Ограничение доступа по `ALLOWED_CHAT_IDS`.
- Набор безопасных команд `/safe` из конфигурации `SAFE_COMMANDS_JSON` (словарь команд).
- Команды для сервисов с ограничениями:
  - `/logs <service> [lines]`
  - `/restart <service>`
  - при заданном `ALLOWED_SERVICES` доступ только к перечисленным сервисам.
- Обмен файлами:
  - загрузка документов в `UPLOAD_DIR` с проверкой размера и расширения;
  - выдача файлов из `DOWNLOAD_DIR` через `/get <filename>`.
- Команды с динамическим выводом (например `top`) принудительно ограничены timeout (5 сек).
- Автозапуск и watchdog через `systemd` (`Restart=on-failure`).

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполните BOT_TOKEN и ALLOWED_CHAT_IDS
python -m tg_admin_bot.bot
```

## Deploy script (Ubuntu)

```bash
sudo bash scripts/deploy_ubuntu.sh
```

Что делает скрипт:
- копирует проект в `/opt/tg-admin-bot`;
- создает пользователя `botuser`;
- создает `.venv` и устанавливает зависимости;
- разворачивает systemd unit;
- включает сервис в автозагрузку;
- запускает сервис, если `.env` содержит реальный токен.

## Установка как service вручную

1. Разверните проект в `/opt/tg-admin-bot`.
2. Создайте пользователя:

```bash
sudo useradd --system --home /opt/tg-admin-bot --shell /usr/sbin/nologin botuser
```

3. Установите unit:

```bash
sudo cp systemd/tg-admin-bot.service /etc/systemd/system/tg-admin-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now tg-admin-bot.service
```

## План развития после MVP

1. Добавить rate-limiting и audit trail в JSON-лог.
2. Добавить подпись артефактов и антивирусную проверку загрузок.
3. Перейти на webhook + reverse proxy (при необходимости).
4. Вынести политики доступа (roles/ACL) в отдельный конфиг.
