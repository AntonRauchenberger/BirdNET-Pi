from __future__ import annotations

import argparse
import csv
import html
import math
from pathlib import Path
from typing import Dict, List, Optional


def _to_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _percentile(values: List[float], q: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _stats(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {
            "avg": None,
            "min": None,
            "max": None,
            "median": None,
            "p95": None,
        }
    return {
        "avg": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "median": _percentile(values, 0.5),
        "p95": _percentile(values, 0.95),
    }


def _fmt(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "NA"
    return f"{value:.{digits}f}"


def _timestamp_to_curve_filename(timestamp: str) -> str:
    return timestamp.replace(":", '"') + "_performance_curve.csv"


def _extract_time_and_series(curve_rows: List[Dict[str, str]], field: str) -> tuple[List[float], List[float]]:
    times: List[float] = []
    values: List[float] = []
    for idx, row in enumerate(curve_rows):
        value = _to_float(row.get(field, ""))
        if value is None:
            continue
        t = _to_float(row.get("timestamp_s", ""))
        if t is None:
            t = float(idx)
        times.append(t)
        values.append(value)
    return times, values


def _scaled_range(min_v: float, max_v: float, pad_fraction: float = 0.05) -> tuple[float, float]:
    if math.isclose(min_v, max_v):
        base = abs(min_v) if min_v else 1.0
        delta = max(0.1, base * 0.05)
        return min_v - delta, max_v + delta
    span = max_v - min_v
    pad = span * pad_fraction
    return min_v - pad, max_v + pad


def _build_path(xs: List[float], ys: List[float], map_x, map_y) -> str:
    if not xs or not ys or len(xs) != len(ys):
        return ""
    points = [f"{map_x(x):.2f},{map_y(y):.2f}" for x, y in zip(xs, ys)]
    return "M" + " L".join(points)


def _phase_color(phase_name: str) -> str:
    palette = [
        "#7B61FF",
        "#17A398",
        "#F39C12",
        "#E74C3C",
        "#2E86DE",
        "#8E44AD",
        "#16A085",
        "#C0392B",
    ]
    return palette[hash(phase_name.strip().lower()) % len(palette)]


def _extract_phase_change_markers(curve_rows: List[Dict[str, str]]) -> List[tuple[float, str]]:
    markers: List[tuple[float, str]] = []
    prev_phase: Optional[str] = None
    for idx, row in enumerate(curve_rows):
        phase = row.get("phase", "").strip()
        if not phase:
            continue
        if prev_phase is None:
            prev_phase = phase
            continue
        if phase != prev_phase:
            t = _to_float(row.get("timestamp_s", ""))
            if t is None:
                t = float(idx)
            markers.append((t, phase))
            prev_phase = phase
    return markers


def _generate_single_metric_svg(
    times: List[float],
    values: List[float],
    title: str,
    y_label: str,
    line_color: str,
    phase_markers: Optional[List[tuple[float, str]]] = None,
    width: int = 520,
    height: int = 260,
) -> str:
    if not times or not values:
        return '<div class="chart-missing">Keine Kurvendaten</div>'

    left, right, top, bottom = 68, 20, 28, 54
    plot_w = width - left - right
    plot_h = height - top - bottom

    x_min, x_max = min(times), max(times)
    if math.isclose(x_min, x_max):
        x_max = x_min + 1.0
    y_min, y_max = _scaled_range(min(values), max(values), 0.08)

    def map_x(x: float) -> float:
        return left + ((x - x_min) / (x_max - x_min)) * plot_w

    def map_y(y: float) -> float:
        return top + ((y_max - y) / (y_max - y_min)) * plot_h

    path = _build_path(times, values, map_x, map_y)
    elements = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(title)}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fff" stroke="#ccd2da"/>',
    ]

    x_ticks = 6
    y_ticks = 5
    for i in range(x_ticks):
        ratio = i / (x_ticks - 1)
        x = left + ratio * plot_w
        x_val = x_min + ratio * (x_max - x_min)
        elements.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#ecf0f4"/>')
        elements.append(
            f'<text x="{x:.2f}" y="{height - 24}" text-anchor="middle" font-size="11" fill="#4b5a6a">{x_val:.1f}</text>'
        )

    for i in range(y_ticks):
        ratio = i / (y_ticks - 1)
        y = top + ratio * plot_h
        y_val = y_max - ratio * (y_max - y_min)
        elements.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#ecf0f4"/>')
        elements.append(
            f'<text x="{left - 8}" y="{y + 4:.2f}" text-anchor="end" font-size="11" fill="#4b5a6a">{y_val:.1f}</text>'
        )

    if phase_markers:
        for idx, (phase_t, phase_name) in enumerate(phase_markers):
            if phase_t < x_min or phase_t > x_max:
                continue
            x = map_x(phase_t)
            color = _phase_color(phase_name)
            label_y = top + 12 + ((idx % 2) * 10)
            elements.append(
                f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="{color}" stroke-dasharray="4 3" stroke-width="1.4"/>'
            )
            elements.append(
                f'<text x="{x + 3:.2f}" y="{label_y}" font-size="10" fill="{color}">{html.escape(phase_name)}</text>'
            )

    elements.extend(
        [
            f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#c8d2dd"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#c8d2dd"/>',
            f'<path d="{path}" fill="none" stroke="{line_color}" stroke-width="2.4"/>',
            f'<text x="{width / 2:.2f}" y="18" text-anchor="middle" font-size="13" fill="#2f3f4f">{html.escape(title)}</text>',
            f'<text x="{width / 2:.2f}" y="{height - 6}" text-anchor="middle" font-size="12" fill="#2f3f4f">Zeit (s)</text>',
            f'<text x="16" y="{height / 2:.2f}" transform="rotate(-90 16 {height / 2:.2f})" text-anchor="middle" font-size="12" fill="#2f3f4f">{html.escape(y_label)}</text>',
            "</svg>",
        ]
    )
    return "".join(elements)


def _generate_combined_svg(
    times_ram: List[float],
    ram_values: List[float],
    times_cpu: List[float],
    cpu_values: List[float],
    phase_markers: Optional[List[tuple[float, str]]] = None,
    width: int = 520,
    height: int = 260,
) -> str:
    if not ram_values and not cpu_values:
        return '<div class="chart-missing">Keine Kurvendaten</div>'

    left, right, top, bottom = 68, 68, 28, 54
    plot_w = width - left - right
    plot_h = height - top - bottom

    all_times = (times_ram or []) + (times_cpu or [])
    x_min = min(all_times) if all_times else 0.0
    x_max = max(all_times) if all_times else 1.0
    if math.isclose(x_min, x_max):
        x_max = x_min + 1.0

    ram_min, ram_max = _scaled_range(min(ram_values), max(ram_values), 0.08) if ram_values else (0.0, 1.0)
    cpu_min, cpu_max = _scaled_range(min(cpu_values), max(cpu_values), 0.08) if cpu_values else (0.0, 1.0)

    def map_x(x: float) -> float:
        return left + ((x - x_min) / (x_max - x_min)) * plot_w

    def map_ram(y: float) -> float:
        return top + ((ram_max - y) / (ram_max - ram_min)) * plot_h

    def map_cpu(y: float) -> float:
        return top + ((cpu_max - y) / (cpu_max - cpu_min)) * plot_h

    ram_path = _build_path(times_ram, ram_values, map_x, map_ram)
    cpu_path = _build_path(times_cpu, cpu_values, map_x, map_cpu)

    elements = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RAM und CPU kombiniert">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fff" stroke="#ccd2da"/>',
    ]

    x_ticks = 6
    y_ticks = 5
    for i in range(x_ticks):
        ratio = i / (x_ticks - 1)
        x = left + ratio * plot_w
        x_val = x_min + ratio * (x_max - x_min)
        elements.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#ecf0f4"/>')
        elements.append(
            f'<text x="{x:.2f}" y="{height - 24}" text-anchor="middle" font-size="11" fill="#4b5a6a">{x_val:.1f}</text>'
        )

    for i in range(y_ticks):
        ratio = i / (y_ticks - 1)
        y = top + ratio * plot_h
        ram_val = ram_max - ratio * (ram_max - ram_min)
        cpu_val = cpu_max - ratio * (cpu_max - cpu_min)
        elements.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#ecf0f4"/>')
        elements.append(
            f'<text x="{left - 8}" y="{y + 4:.2f}" text-anchor="end" font-size="11" fill="#0072B2">{ram_val:.1f}</text>'
        )
        elements.append(
            f'<text x="{left + plot_w + 8}" y="{y + 4:.2f}" text-anchor="start" font-size="11" fill="#D55E00">{cpu_val:.1f}</text>'
        )

    if phase_markers:
        for idx, (phase_t, phase_name) in enumerate(phase_markers):
            if phase_t < x_min or phase_t > x_max:
                continue
            x = map_x(phase_t)
            color = _phase_color(phase_name)
            label_y = top + 12 + ((idx % 2) * 10)
            elements.append(
                f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="{color}" stroke-dasharray="4 3" stroke-width="1.4"/>'
            )
            elements.append(
                f'<text x="{x + 3:.2f}" y="{label_y}" font-size="10" fill="{color}">{html.escape(phase_name)}</text>'
            )

    elements.extend(
        [
            f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#c8d2dd"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#c8d2dd"/>',
            f'<line x1="{left + plot_w}" y1="{top}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#c8d2dd"/>',
        ]
    )
    if ram_path:
        elements.append(f'<path d="{ram_path}" fill="none" stroke="#0072B2" stroke-width="2.4"/>')
    if cpu_path:
        elements.append(f'<path d="{cpu_path}" fill="none" stroke="#D55E00" stroke-width="2.4"/>')

    elements.extend(
        [
            f'<text x="{width / 2:.2f}" y="18" text-anchor="middle" font-size="13" fill="#2f3f4f">RAM + CPU kombiniert</text>',
            f'<text x="{width / 2:.2f}" y="{height - 6}" text-anchor="middle" font-size="12" fill="#2f3f4f">Zeit (s)</text>',
            f'<text x="16" y="{height / 2:.2f}" transform="rotate(-90 16 {height / 2:.2f})" text-anchor="middle" font-size="12" fill="#0072B2">RAM (MB)</text>',
            f'<text x="{width - 14}" y="{height / 2:.2f}" transform="rotate(90 {width - 14} {height / 2:.2f})" text-anchor="middle" font-size="12" fill="#D55E00">CPU (%)</text>',
            f'<line x1="{left + 12}" y1="{top + 10}" x2="{left + 30}" y2="{top + 10}" stroke="#0072B2" stroke-width="2.4"/>',
            f'<text x="{left + 34}" y="{top + 14}" font-size="11" fill="#2f3f4f">RAM</text>',
            f'<line x1="{left + 78}" y1="{top + 10}" x2="{left + 96}" y2="{top + 10}" stroke="#D55E00" stroke-width="2.4"/>',
            f'<text x="{left + 100}" y="{top + 14}" font-size="11" fill="#2f3f4f">CPU</text>',
            "</svg>",
        ]
    )

    return "".join(elements)


def _generate_svg(curve_rows: List[Dict[str, str]]) -> str:
    times_ram, ram_values = _extract_time_and_series(curve_rows, "ram_mb_birdnet_process")
    times_cpu, cpu_values = _extract_time_and_series(curve_rows, "cpu_percent_birdnet_process")
    phase_markers = _extract_phase_change_markers(curve_rows)

    ram_svg = _generate_single_metric_svg(
        times=times_ram,
        values=ram_values,
        title="RAM-Verlauf pro Testdurchlauf",
        y_label="RAM (MB)",
        line_color="#0072B2",
        phase_markers=phase_markers,
    )
    cpu_svg = _generate_single_metric_svg(
        times=times_cpu,
        values=cpu_values,
        title="CPU-Verlauf pro Testdurchlauf",
        y_label="CPU (%)",
        line_color="#D55E00",
        phase_markers=phase_markers,
    )
    combined_svg = _generate_combined_svg(times_ram, ram_values, times_cpu, cpu_values, phase_markers=phase_markers)

    return (
        '<div class="charts-grid">'
        f'<div class="chart-card">{ram_svg}</div>'
        f'<div class="chart-card">{cpu_svg}</div>'
        f'<div class="chart-card">{combined_svg}</div>'
        "</div>"
    )


def _read_metrics_file(path: Path) -> tuple[str, List[Dict[str, str]], List[str]]:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("Timestamp,"):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"Keine Metrik-Tabelle in {path} gefunden.")

    metadata_lines = lines[:header_idx]
    csv_text = "\n".join(lines[header_idx:])
    reader = csv.DictReader(csv_text.splitlines())
    rows = [dict(row) for row in reader]
    columns = list(reader.fieldnames or [])
    return "\n".join(metadata_lines), rows, columns


def _read_curve_file(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _calculate_curve_summary(curve_rows: List[Dict[str, str]]) -> Dict[str, str]:
    timestamps = [_to_float(r.get("timestamp_s", "")) for r in curve_rows]
    timestamps = [v for v in timestamps if v is not None]

    ram_process = [_to_float(r.get("ram_mb_birdnet_process", "")) for r in curve_rows]
    ram_process = [v for v in ram_process if v is not None]

    total_used_percent = [_to_float(r.get("total_used_ram_percent", "")) for r in curve_rows]
    total_used_percent = [v for v in total_used_percent if v is not None]

    cpu_process = [_to_float(r.get("cpu_percent_birdnet_process", "")) for r in curve_rows]
    cpu_process = [v for v in cpu_process if v is not None]

    cpu_system = [_to_float(r.get("cpu_percent_system", "")) for r in curve_rows]
    cpu_system = [v for v in cpu_system if v is not None]

    phase_values = [r.get("phase", "").strip().lower() for r in curve_rows]
    analysis_samples = sum(1 for p in phase_values if p == "analysis")
    idle_samples = sum(1 for p in phase_values if p == "idle")

    duration = None
    if timestamps:
        duration = max(timestamps) - min(timestamps)

    ram_stats = _stats(ram_process)
    used_stats = _stats(total_used_percent)
    cpu_p_stats = _stats(cpu_process)
    cpu_s_stats = _stats(cpu_system)

    return {
        "samples": str(len(curve_rows)),
        "duration_s": _fmt(duration, 3),
        "analysis_samples": str(analysis_samples),
        "idle_samples": str(idle_samples),
        "ram_avg_mb": _fmt(ram_stats["avg"]),
        "ram_min_mb": _fmt(ram_stats["min"]),
        "ram_max_mb": _fmt(ram_stats["max"]),
        "ram_p95_mb": _fmt(ram_stats["p95"]),
        "used_ram_avg_pct": _fmt(used_stats["avg"]),
        "used_ram_max_pct": _fmt(used_stats["max"]),
        "cpu_proc_avg_pct": _fmt(cpu_p_stats["avg"]),
        "cpu_proc_max_pct": _fmt(cpu_p_stats["max"]),
        "cpu_proc_p95_pct": _fmt(cpu_p_stats["p95"]),
        "cpu_sys_avg_pct": _fmt(cpu_s_stats["avg"]),
        "cpu_sys_max_pct": _fmt(cpu_s_stats["max"]),
    }


def _aggregate_all_curves(curve_files: List[Path]) -> tuple[List[float], List[float], List[float], List[float], List[tuple[float, str]]]:
    """Aggregates all curve data by computing average values at normalized time positions."""
    all_times_ram: List[List[float]] = []
    all_values_ram: List[List[float]] = []
    all_times_cpu: List[List[float]] = []
    all_values_cpu: List[List[float]] = []
    all_phase_markers_normalized: List[List[tuple[float, str]]] = []

    for curve_file in curve_files:
        if not curve_file.exists():
            continue
        curve_rows = _read_curve_file(curve_file)
        times_ram, ram_vals = _extract_time_and_series(curve_rows, "ram_mb_birdnet_process")
        times_cpu, cpu_vals = _extract_time_and_series(curve_rows, "cpu_percent_birdnet_process")

        if times_ram and ram_vals:
            all_times_ram.append(times_ram)
            all_values_ram.append(ram_vals)
        if times_cpu and cpu_vals:
            all_times_cpu.append(times_cpu)
            all_values_cpu.append(cpu_vals)

        timestamps = [_to_float(r.get("timestamp_s", "")) for r in curve_rows]
        timestamps = [v for v in timestamps if v is not None]
        if timestamps:
            t_min = min(timestamps)
            t_max = max(timestamps)
            duration = max(1e-6, t_max - t_min)
            markers = _extract_phase_change_markers(curve_rows)
            normalized_markers = [((t - t_min) / duration, phase) for t, phase in markers]
            all_phase_markers_normalized.append(normalized_markers)

    # Normalize curves to 100 points each and compute averages
    def normalize_and_average(times_list: List[List[float]], values_list: List[List[float]]) -> tuple[List[float], List[float], float]:
        if not times_list:
            return [], [], 0.0

        num_points = 100
        normalized_values = []
        durations: List[float] = []

        for times, values in zip(times_list, values_list):
            if not times or not values:
                continue
            t_min, t_max = min(times), max(times)
            if math.isclose(t_min, t_max):
                t_max = t_min + 1.0
            durations.append(t_max - t_min)
            
            # Interpolate to num_points
            interp_times = [t_min + i * (t_max - t_min) / (num_points - 1) for i in range(num_points)]
            interp_values = []
            for t in interp_times:
                idx = next((i for i, tm in enumerate(times) if tm >= t), len(times) - 1)
                if idx == 0:
                    interp_values.append(values[0])
                else:
                    t0, t1 = times[idx - 1], times[idx]
                    v0, v1 = values[idx - 1], values[idx]
                    if math.isclose(t0, t1):
                        interp_values.append(v0)
                    else:
                        frac = (t - t0) / (t1 - t0)
                        interp_values.append(v0 * (1 - frac) + v1 * frac)
            normalized_values.append(interp_values)

        if not normalized_values:
            return [], [], 0.0

        # Average across runs
        avg_values = [sum(col) / len(col) for col in zip(*normalized_values)]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        avg_times = [i * avg_duration / (num_points - 1) for i in range(num_points)]
        return avg_times, avg_values, avg_duration

    def aggregate_phase_markers(
        normalized_sequences: List[List[tuple[float, str]]], duration: float
    ) -> List[tuple[float, str]]:
        buckets: Dict[tuple[int, str], List[float]] = {}
        for sequence in normalized_sequences:
            for idx, (norm_t, phase_name) in enumerate(sequence):
                key = (idx, phase_name)
                buckets.setdefault(key, []).append(norm_t)

        aggregated: List[tuple[float, str]] = []
        for (idx, phase_name), values in buckets.items():
            _ = idx
            avg_norm_t = sum(values) / len(values)
            aggregated.append((avg_norm_t * duration, phase_name))

        return sorted(aggregated, key=lambda item: item[0])

    avg_times_ram, avg_ram, avg_duration_ram = normalize_and_average(all_times_ram, all_values_ram)
    avg_times_cpu, avg_cpu, avg_duration_cpu = normalize_and_average(all_times_cpu, all_values_cpu)

    marker_duration = max(avg_duration_ram, avg_duration_cpu, 0.0)
    aggregated_phase_markers = aggregate_phase_markers(all_phase_markers_normalized, marker_duration)

    return avg_times_ram, avg_ram, avg_times_cpu, avg_cpu, aggregated_phase_markers


def _generate_aggregated_summary_stats(merged_rows: List[Dict[str, str]]) -> Dict[str, str]:
    """Generates summary statistics across all test runs."""

    def get_row_float(row: Dict[str, str], field: str) -> Optional[float]:
        value = row.get(field, "")
        if value in (None, ""):
            field_norm = field.strip()
            for key, raw in row.items():
                if key.strip() == field_norm:
                    value = raw
                    break
        return _to_float(value)

    # Extract numeric values from merged_rows for each metric
    metric_fields = [
        ("Avg Confidence (%)", "Avg Confidence (%)"),
        ("Total Analysis (s)", "Total Analysis (s)"),
        ("Inference (s)", "Inference (s)"),
        ("Model Load (s)", "Model Load (s)"),
        ("Audio Processing (s)", "Audio Processing (s)"),
        ("Total Reporting (s)", "Total Reporting (s)"),
        ("ram_avg_mb", "RAM Average (MB)"),
        ("ram_max_mb", "RAM Peak (MB)"),
        ("ram_p95_mb", "RAM p95 (MB)"),
        ("cpu_proc_avg_pct", "CPU Process Avg (%)"),
        ("cpu_proc_max_pct", "CPU Process Peak (%)"),
        ("cpu_proc_p95_pct", "CPU Process p95 (%)"),
        ("cpu_sys_avg_pct", "CPU System Avg (%)"),
        ("cpu_sys_max_pct", "CPU System Peak (%)"),
        ("duration_s", "Test Duration (s)"),
    ]

    stats = {}
    for field, label in metric_fields:
        values = [get_row_float(row, field) for row in merged_rows]
        values = [v for v in values if v is not None]
        field_stats = _stats(values)
        stats[f"{field}_avg"] = _fmt(field_stats["avg"])
        stats[f"{field}_min"] = _fmt(field_stats["min"])
        stats[f"{field}_max"] = _fmt(field_stats["max"])

    total_runs = len(merged_rows)
    stats["total_runs"] = str(total_runs)

    return stats


def _build_html_report(
    metadata_block: str,
    metric_columns: List[str],
    merged_rows: List[Dict[str, str]],
    curves_dir: Path,
    output_path: Path,
) -> None:
    summary_columns = [
        "samples",
        "duration_s",
        "analysis_samples",
        "idle_samples",
        "ram_avg_mb",
        "ram_min_mb",
        "ram_max_mb",
        "ram_p95_mb",
        "used_ram_avg_pct",
        "used_ram_max_pct",
        "cpu_proc_avg_pct",
        "cpu_proc_max_pct",
        "cpu_proc_p95_pct",
        "cpu_sys_avg_pct",
        "cpu_sys_max_pct",
    ]

    # Generate summary section with aggregated stats and graphs
    summary_stats = _generate_aggregated_summary_stats(merged_rows)
    
    # Get all curve files for aggregation
    curve_files = sorted(curves_dir.glob("*_performance_curve.csv")) if curves_dir.exists() else []
    avg_times_ram, avg_ram, avg_times_cpu, avg_cpu, aggregated_phase_markers = _aggregate_all_curves(curve_files)
    
    # Generate aggregated SVGs
    ram_svg = _generate_single_metric_svg(
        times=avg_times_ram,
        values=avg_ram,
        title="Durchschnittlicher RAM-Verlauf (über alle Durchläufe)",
        y_label="RAM (MB)",
        line_color="#0072B2",
        phase_markers=aggregated_phase_markers,
    )
    cpu_svg = _generate_single_metric_svg(
        times=avg_times_cpu,
        values=avg_cpu,
        title="Durchschnittlicher CPU-Verlauf (über alle Durchläufe)",
        y_label="CPU (%)",
        line_color="#D55E00",
        phase_markers=aggregated_phase_markers,
    )
    combined_svg = _generate_combined_svg(
        avg_times_ram,
        avg_ram,
        avg_times_cpu,
        avg_cpu,
        phase_markers=aggregated_phase_markers,
    )
    
    # Build summary table HTML
    summary_table_rows = []
    metric_labels = {
        "Avg Confidence (%)": "Avg Confidence (%)",
        "Total Analysis (s)": "Total Analysis (s)",
        "Inference (s)": "Inference (s)",
        "Model Load (s)": "Model Load (s)",
        "Audio Processing (s)": "Audio Processing (s)",
        "Total Reporting (s)": "Total Reporting (s)",
        "ram_avg_mb": "RAM Avg (MB)",
        "ram_max_mb": "RAM Max (MB)",
        "ram_p95_mb": "RAM p95 (MB)",
        "cpu_proc_avg_pct": "CPU Proc Avg (%)",
        "cpu_proc_max_pct": "CPU Proc Max (%)",
        "cpu_proc_p95_pct": "CPU Proc p95 (%)",
        "cpu_sys_avg_pct": "CPU Sys Avg (%)",
        "cpu_sys_max_pct": "CPU Sys Max (%)",
        "duration_s": "Duration (s)",
    }
    
    for field, label in metric_labels.items():
        avg_val = summary_stats.get(f"{field}_avg", "NA")
        min_val = summary_stats.get(f"{field}_min", "NA")
        max_val = summary_stats.get(f"{field}_max", "NA")
        summary_table_rows.append(
            f"<tr><td>{html.escape(label)}</td><td>{html.escape(avg_val)}</td><td>{html.escape(min_val)}</td><td>{html.escape(max_val)}</td></tr>"
        )
    
    summary_table_html = f"""
        <table class="summary-table">
      <thead>
        <tr>
          <th>Metrik</th>
          <th>Durchschnitt</th>
          <th>Minimum</th>
          <th>Maximum</th>
        </tr>
      </thead>
      <tbody>
        {''.join(summary_table_rows)}
      </tbody>
    </table>
    """

    summary_section_html = f"""
    <section class="panel">
      <h2>Zusammenfassung über alle Testdurchläufe</h2>
      <p><strong>Anzahl Testdurchläufe:</strong> {summary_stats.get('total_runs', 'N/A')}</p>
      <div class="table-wrap">
        {summary_table_html}
      </div>
      <h3 style="margin-top: 1.5rem;">Aggregierte Messwerte</h3>
      <div class="charts-grid" style="display: flex; overflow: auto;">
        <div class="chart-card">{ram_svg}</div>
        <div class="chart-card">{cpu_svg}</div>
        <div class="chart-card">{combined_svg}</div>
      </div>
    </section>
    """

    # Generate detail rows
    header_cells = "".join(f"<th>{html.escape(col)}</th>" for col in metric_columns + summary_columns)
    header_cells += "<th>Curve Diagram</th>"

    body_rows = []
    for row in merged_rows:
        values = [html.escape(row.get(col, "")) for col in metric_columns + summary_columns]
        metric_cells = "".join(f"<td>{val}</td>" for val in values)
        chart_cell = f"<td>{row.get('_curve_svg', '')}</td>"
        body_rows.append(f"<tr>{metric_cells}{chart_cell}</tr>")

    html_content = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Benchmark Zusammenfassung</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --panel: #ffffff;
      --text: #1f2d3d;
      --line: #d3dce6;
      --head: #e8eef6;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "DejaVu Sans", "Noto Sans", sans-serif;
    }}
    main {{
      max-width: 1800px;
      margin: 1rem auto;
      padding: 0 1rem;
    }}
    h1 {{
      margin: 0 0 0.5rem;
      font-size: 1.5rem;
    }}
    h2 {{
      margin-top: 0;
      margin-bottom: 1rem;
      font-size: 1.2rem;
    }}
    h3 {{
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      font-size: 1rem;
    }}
    p {{
      margin: 0.25rem 0;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      font-family: "DejaVu Sans Mono", "Noto Sans Mono", monospace;
      font-size: 0.92rem;
    }}
    .table-wrap {{
      overflow-x: auto;
      margin: 0.5rem 0;
    }}
    table {{
      border-collapse: collapse;
      width: max-content;
      min-width: 100%;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 0.4rem 0.5rem;
      vertical-align: top;
      white-space: nowrap;
      font-size: 0.86rem;
    }}
    th {{
      background: var(--head);
      position: sticky;
      top: 0;
      z-index: 2;
    }}
        .details-table td:last-child {{
        min-width: 1620px;
    }}
        .summary-table {{
            width: auto;
        }}
    .charts-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(520px, 1fr));
        gap: 0.6rem;
        margin-top: 0.5rem;
    }}
    .chart-card {{
        border: 1px solid #d7dee8;
        border-radius: 6px;
        background: #fafcff;
        padding: 0.2rem;
    }}
    .chart-card svg {{
        display: block;
    }}
    .chart-missing {{
      color: #7f8c99;
      font-style: italic;
      padding: 0.5rem;
    }}
  </style>
</head>
<body>
  <main>
    <h1>BirdNET Benchmark Report</h1>
    <section class="panel">
      <h2>Allgemeine Informationen</h2>
      <pre>{html.escape(metadata_block)}</pre>
    </section>
    {summary_section_html}
    <section class="panel table-wrap">
      <h2>Details der Durchläufe mit Kennzahlen und Kurven</h2>
            <table class="details-table">
        <thead>
          <tr>{header_cells}</tr>
        </thead>
        <tbody>
          {''.join(body_rows)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""

    output_path.write_text(html_content, encoding="utf-8")


def create_summary(metrics_file: Path, curves_dir: Path, output_file: Path) -> None:
    metadata_block, metrics_rows, metric_columns = _read_metrics_file(metrics_file)

    merged_rows: List[Dict[str, str]] = []
    for metric_row in metrics_rows:
        timestamp = metric_row.get("Timestamp", "").strip()
        curve_name = _timestamp_to_curve_filename(timestamp)
        curve_path = curves_dir / curve_name

        row_data = dict(metric_row)
        if curve_path.exists():
            curve_rows = _read_curve_file(curve_path)
            row_data.update(_calculate_curve_summary(curve_rows))
            row_data["_curve_svg"] = _generate_svg(curve_rows)
        else:
            row_data.update(
                {
                    "samples": "0",
                    "duration_s": "NA",
                    "analysis_samples": "0",
                    "idle_samples": "0",
                    "ram_avg_mb": "NA",
                    "ram_min_mb": "NA",
                    "ram_max_mb": "NA",
                    "ram_p95_mb": "NA",
                    "used_ram_avg_pct": "NA",
                    "used_ram_max_pct": "NA",
                    "cpu_proc_avg_pct": "NA",
                    "cpu_proc_max_pct": "NA",
                    "cpu_proc_p95_pct": "NA",
                    "cpu_sys_avg_pct": "NA",
                    "cpu_sys_max_pct": "NA",
                }
            )
            row_data["_curve_svg"] = '<div class="chart-missing">Curve-Datei nicht gefunden</div>'

        merged_rows.append(row_data)

    _build_html_report(metadata_block, metric_columns, merged_rows, curves_dir, output_file)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    default_input_dir = project_root / "tests" / "testdata" / "evaluating" / "Pi4B"

    parser = argparse.ArgumentParser(
        description="Erstellt einen zusammengefassten BirdNET-Benchmark-Report aus metrics_log.csv und curves/*.csv"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=default_input_dir,
        help="Ordner mit metrics_log.csv und curves/",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Ausgabe-Datei (default: <input-dir>/benchmark_summary.html)",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    metrics_file = input_dir / "metrics_log.csv"
    curves_dir = input_dir / "curves"
    output_file = (args.output.resolve() if args.output else (input_dir / "benchmark_summary.html").resolve())

    if not metrics_file.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {metrics_file}")
    if not curves_dir.exists():
        raise FileNotFoundError(f"Ordner nicht gefunden: {curves_dir}")

    create_summary(metrics_file, curves_dir, output_file)
    print(f"Report erstellt: {output_file}")


if __name__ == "__main__":
    main()