#!/usr/bin/env bash
set -euo pipefail

# Run full BirdNET-Pi benchmarking setup and tests:
# 1) install sox
# 2) prepare an isolated benchmark config from tests/testdata/test_birdnet.conf
# 3) run benchmark-related tests

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
CONF_SOURCE="${REPO_DIR}/tests/testdata/test_birdnet.conf"
CONF_TARGET=""
CONSTANTS_FILE="${REPO_DIR}/scripts/utils/constants.py"

cleanup() {
	if [[ -n "${CONF_TARGET}" && -f "${CONF_TARGET}" ]]; then
		rm -f "${CONF_TARGET}"
	fi
}
trap cleanup EXIT

if [[ "${EUID}" -ne 0 ]]; then
	exec sudo bash "$0" "$@"
fi

SCENARIO_NAME="${1:-}"
BENCHMARK_RUNS="${2:-10}"
EVALUATE="${3:-false}"
if [[ -z "${SCENARIO_NAME}" ]]; then
	read -r -p "Enter benchmark scenario name (e.g. Pi4, Pi Zero, Local Laptop): " SCENARIO_NAME
fi

if [[ -z "${SCENARIO_NAME}" ]]; then
	echo "Error: scenario name must not be empty." >&2
	exit 1
fi

if ! [[ "${BENCHMARK_RUNS}" =~ ^[1-9][0-9]*$ ]]; then
	echo "Error: repeats must be a positive integer." >&2
	exit 1
fi

EVALUATE="${EVALUATE,,}"
if [[ "${EVALUATE}" != "true" && "${EVALUATE}" != "false" ]]; then
	echo "Error: evaluate must be either 'true' or 'false'." >&2
	exit 1
fi

echo "[1/5] Checking prerequisites..."
if [[ ! -f "${CONF_SOURCE}" ]]; then
	echo "Error: Missing config template: ${CONF_SOURCE}" >&2
	exit 1
fi
if [[ ! -f "${CONSTANTS_FILE}" ]]; then
	echo "Error: Missing constants file: ${CONSTANTS_FILE}" >&2
	exit 1
fi

echo "[2/5] Installing sox..."
apt-get update
apt-get install -y sox

CONF_TARGET="$(mktemp /tmp/birdnet-benchmark-conf.XXXXXX.conf)"
echo "[3/5] Preparing isolated benchmark config at ${CONF_TARGET}..."
install -m 0600 "${CONF_SOURCE}" "${CONF_TARGET}"

echo "[3b/5] Adjusting config paths for current user..."
CURRENT_USER="${SUDO_USER:-$(id -un)}"
CURRENT_HOME="$(getent passwd "${CURRENT_USER}" | cut -d: -f6)"
if [[ -z "${CURRENT_HOME}" ]]; then
	CURRENT_HOME="$(eval echo ~"${CURRENT_USER}")"
fi
BIRD_SONGS_DIR="${CURRENT_HOME}/BirdSongs"

# Create the required directories
mkdir -p "${BIRD_SONGS_DIR}/Extracted/By_Date"
mkdir -p "${BIRD_SONGS_DIR}/Processed"

# Update paths in the config file
sed -i "s|RECS_DIR=.*|RECS_DIR=${BIRD_SONGS_DIR}|" "${CONF_TARGET}"
sed -i "s|EXTRACTED=.*|EXTRACTED=${BIRD_SONGS_DIR}/Extracted|" "${CONF_TARGET}"
sed -i "s|PROCESSED=.*|PROCESSED=${BIRD_SONGS_DIR}/Processed|" "${CONF_TARGET}"

echo "Paths updated for user ${CURRENT_USER}: ${BIRD_SONGS_DIR}"

echo "[4/5] Setting scenario in constants.py..."
python - "${CONSTANTS_FILE}" "${SCENARIO_NAME}" <<'PY'
import pathlib
import re
import sys

constants_file = pathlib.Path(sys.argv[1])
scenario_name = sys.argv[2]
content = constants_file.read_text(encoding="utf-8")

updated, count = re.subn(
    r'^BENCHMARKING_SCENARIO\s*=\s*".*"\s*$',
    f'BENCHMARKING_SCENARIO = "{scenario_name}"',
    content,
    count=1,
    flags=re.MULTILINE,
)

if count != 1:
    raise SystemExit("Failed to update BENCHMARKING_SCENARIO in constants.py")

constants_file.write_text(updated, encoding="utf-8")
print(f"Scenario set to: {scenario_name}")
PY

echo "[5/5] Running benchmark tests (${BENCHMARK_RUNS}x full pipeline)..."
cd "${REPO_DIR}"
source birdnet/bin/activate

if ! command -v unshare >/dev/null 2>&1; then
	echo "Error: 'unshare' is required for isolated benchmark config handling." >&2
	exit 1
fi

for ((run = 1; run <= BENCHMARK_RUNS; run++)); do
	echo "----- Full benchmark run ${run}/${BENCHMARK_RUNS} -----"
	unshare --mount --propagation private bash -euo pipefail -c '
		mkdir -p /etc/birdnet
		if [[ ! -f /etc/birdnet/birdnet.conf ]]; then
			touch /etc/birdnet/birdnet.conf
		fi
		mount --bind "$1" /etc/birdnet/birdnet.conf
		python -m pytest -q -s tests/test_full_benchmark.py -k test_full_pipeline_benchmark
	' _ "${CONF_TARGET}"
done

if [[ "${EVALUATE}" == "true" ]]; then
	echo "[6/6] Running evaluation for scenario ${SCENARIO_NAME}..."
	cd "${SCRIPT_DIR}"
	sudo ./evaluating.sh "${SCENARIO_NAME}"
fi

echo "Done: Benchmark setup + scenario update + ${BENCHMARK_RUNS} test runs completed successfully."
