#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
TARGET_DIR="${PROJECT_ROOT}/web-app-dist"

echo "Running npm run build..."
cd "${SCRIPT_DIR}"
npm run build

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "No web-app-dist found. Creating it..."
  mkdir -p "${TARGET_DIR}"
fi

echo "Syncing ${DIST_DIR} -> ${TARGET_DIR}"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "${DIST_DIR}/" "${TARGET_DIR}/"
else
  rm -rf "${TARGET_DIR}"
  mkdir -p "${TARGET_DIR}"
  cp -a "${DIST_DIR}/." "${TARGET_DIR}/"
fi

echo "Done. web-app-dist now matches app/dist."
