#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

PULL_OUTPUT="$(git pull origin main)"
echo "$PULL_OUTPUT"

if [[ "$PULL_OUTPUT" == *"Already up to date."* ]]; then
  echo "Already up to date. No reboot needed."
  exit 0
fi

echo "Update successful, rebooting..."
sudo reboot