#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
	echo "Usage: $0 <scenario-name>" >&2
	exit 1
fi

scenario_name="$1"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "$script_dir/.." && pwd)"
scenario_dir="$project_root/benchmarking_results/$scenario_name"
python_script="$project_root/scripts/utils/evaluating.py"
venv_python="$project_root/birdnet/bin/python"

if [[ ! -d "$scenario_dir" ]]; then
	echo "Scenario directory not found: $scenario_dir" >&2
	exit 1
fi

if [[ -x "$venv_python" ]]; then
	python_bin="$venv_python"
elif command -v python3 >/dev/null 2>&1; then
	python_bin="$(command -v python3)"
else
	echo "No usable Python interpreter found." >&2
	exit 1
fi

"$python_bin" "$python_script" --scenario "$scenario_name" --output "$scenario_dir/benchmark_summary.html"
