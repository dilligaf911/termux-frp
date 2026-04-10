#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/tg-admin-bot"
SERVICE_NAME="tg-admin-bot"
BOT_USER="botuser"
REPO_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash scripts/deploy_ubuntu.sh"
  exit 1
fi

NEED_PKGS=()
command -v python3 >/dev/null 2>&1 || NEED_PKGS+=(python3 python3-venv python3-pip)
command -v rsync >/dev/null 2>&1 || NEED_PKGS+=(rsync)

if (( ${#NEED_PKGS[@]} > 0 )); then
  apt-get update
  apt-get install -y "${NEED_PKGS[@]}"
fi

id -u "$BOT_USER" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$BOT_USER"

mkdir -p "$APP_DIR"
rsync -a --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  "$REPO_SRC"/ "$APP_DIR"/

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

if [[ ! -f "$APP_DIR/.env" ]]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "Created $APP_DIR/.env from template. Fill BOT_TOKEN and ALLOWED_CHAT_IDS before start."
fi

mkdir -p "$APP_DIR/data/uploads" "$APP_DIR/data/downloads"
chown -R "$BOT_USER:$BOT_USER" "$APP_DIR"

cp "$APP_DIR/systemd/tg-admin-bot.service" "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

if grep -q '^BOT_TOKEN=123456:your-token$' "$APP_DIR/.env"; then
  echo "Service enabled, but not started: update BOT_TOKEN in $APP_DIR/.env"
else
  systemctl restart "$SERVICE_NAME"
  systemctl status "$SERVICE_NAME" --no-pager || true
fi

echo "Deploy complete."
