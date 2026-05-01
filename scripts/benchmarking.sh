#!/usr/bin/env bash
set -euo pipefail

# Run full BirdNET-Pi benchmarking setup and tests:
# 1) install sox
# 2) install /etc/birdnet/birdnet.conf from tests/testdata/test_birdnet.conf
# 3) run benchmark-related tests

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
CONF_SOURCE="${REPO_DIR}/tests/testdata/test_birdnet.conf"
CONF_TARGET_DIR="/etc/birdnet"
CONF_TARGET="${CONF_TARGET_DIR}/birdnet.conf"
CONSTANTS_FILE="${REPO_DIR}/scripts/utils/constants.py"

SCENARIO_NAME="${1:-}"
BENCHMARK_RUNS="${2:-10}"
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
sudo apt-get update
sudo apt-get install -y sox

echo "[3/5] Installing benchmark config to ${CONF_TARGET}..."
sudo mkdir -p "${CONF_TARGET_DIR}"
sudo install -m 0644 "${CONF_SOURCE}" "${CONF_TARGET}"

echo "[3b/5] Adjusting config paths for current user..."
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)
BIRD_SONGS_DIR="${CURRENT_HOME}/BirdSongs"

# Create the required directories
mkdir -p "${BIRD_SONGS_DIR}/Extracted/By_Date"
mkdir -p "${BIRD_SONGS_DIR}/Processed"

# Update paths in the config file
sudo sed -i "s|RECS_DIR=.*|RECS_DIR=${BIRD_SONGS_DIR}|" "${CONF_TARGET}"
sudo sed -i "s|EXTRACTED=.*|EXTRACTED=${BIRD_SONGS_DIR}/Extracted|" "${CONF_TARGET}"
sudo sed -i "s|PROCESSED=.*|PROCESSED=${BIRD_SONGS_DIR}/Processed|" "${CONF_TARGET}"

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

for ((run = 1; run <= BENCHMARK_RUNS; run++)); do
	echo "----- Full benchmark run ${run}/${BENCHMARK_RUNS} -----"
	python -m pytest -q -s tests/test_full_benchmark.py -k test_full_pipeline_benchmark
done

echo "Done: Benchmark setup + scenario update + ${BENCHMARK_RUNS} test runs completed successfully."
