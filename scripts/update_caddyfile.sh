#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  exec sudo -E HOME="${HOME}" USER="${USER}" bash "$0" "$@"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SERVICES_SCRIPT="${SCRIPT_DIR}/install_services.sh"
HELPERS_SCRIPT="${SCRIPT_DIR}/install_helpers.sh"

if [[ ! -f "${INSTALL_SERVICES_SCRIPT}" ]]; then
  echo "install_services.sh not found at ${INSTALL_SERVICES_SCRIPT}" >&2
  exit 1
fi

if [[ ! -f "${HELPERS_SCRIPT}" ]]; then
  echo "install_helpers.sh not found at ${HELPERS_SCRIPT}" >&2
  exit 1
fi

CONFIG_FILE="${SCRIPT_DIR}/birdnet.conf"
if [[ -f "/etc/birdnet/birdnet.conf" ]]; then
  CONFIG_FILE="/etc/birdnet/birdnet.conf"
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "birdnet.conf not found (checked ${SCRIPT_DIR}/birdnet.conf and /etc/birdnet/birdnet.conf)" >&2
  exit 1
fi

# Load installer functions without running the full install routine.
my_dir="/__birdnet_skip_autorun__"
# shellcheck disable=SC1090
source "${INSTALL_SERVICES_SCRIPT}" >/dev/null 2>&1 || true
set +x

my_dir="${SCRIPT_DIR}"
config_file="${CONFIG_FILE}"
# shellcheck disable=SC1090
source "${CONFIG_FILE}"
# shellcheck disable=SC1090
source "${HELPERS_SCRIPT}"

install_Caddyfile

caddy fmt --overwrite /etc/caddy/Caddyfile
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy

echo "Caddyfile updated via install_Caddyfile()."
