#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 username@ipaddress [remote_dir]" >&2
  echo "Example: $0 deploy@192.0.2.10 ~/kiosk_dashboard" >&2
  exit 1
fi

REMOTE="$1"
REMOTE_DIR="${2:-~/kiosk_dashboard}"

rsync -avz --delete \
  --exclude ".git/" \
  --exclude ".DS_Store" \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude ".venv/" \
  --exclude "venv/" \
  --exclude "*.md" \
  --exclude "deploy.sh" \
  --exclude "*.png" \
  --exclude "LICENSE" \
  --exclude "frontend/node_modules/" \
  --exclude "frontend/.svelte-kit/" \
  --exclude "frontend/.vite/" \
  --exclude "frontend/.cache/" \
  ./ "${REMOTE}:${REMOTE_DIR}/"
