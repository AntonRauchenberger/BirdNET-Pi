"""
Reusable monitoring / benchmarking utilities for BirdNET-Pi

Main features:
- Multiple timers at the same time (by name)
- Per-timer averages over multiple runs
- Process RAM usage (RSS) and peaks during timed blocks
- Confidence during prediction
- Flash storage calculations
"""

from __future__ import annotations

import os
import time
import datetime
import threading
import psutil
# import birdnet_analyzer.config as cfg
from dataclasses import dataclass, field
from typing import Any
import shutil

# Binary size units are used (1024 instead of 1000)
def _bytes_to_mb(num_bytes: float) -> float:
    return num_bytes / (1024 * 1024)

def _bytes_to_gb(num_bytes: float) -> float:
    return num_bytes / (1024 * 1024 * 1024)

class MemorySampler(threading.Thread):
    def __init__(self, service_ref, interval=0.01): # 10 ms so ram use measurements are not disturbed
        super().__init__()
        self.service = service_ref
        self.interval = interval
        self.peak_ram = 0.0
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            # Aktuellen RAM abfragen
            current_ram = self.service.get_ram_usage_mb()
            if current_ram > self.peak_ram:
                self.peak_ram = current_ram
            time.sleep(self.interval)

    def stop(self):
        self._stop_event.set()
        return self.peak_ram

@dataclass
class _TimerRun:
    """Stores raw data for one timer run (start -> stop)."""

    wall_seconds: float
    cpu_seconds: float
    rss_start_bytes: int # Needed RAM storage at the start
    rss_end_bytes: int
    peak_interval_mb: float = 0.0 # peak ram usage during measurement

    @property
    def rss_delta_bytes(self) -> int:
        return self.rss_end_bytes - self.rss_start_bytes


@dataclass
class _TimerStats:
    """Aggregates multiple runs for a single named timer, calculates average values."""

    runs: list[_TimerRun] = field(default_factory=list)

    def add_run(self, run: _TimerRun) -> None:
        self.runs.append(run)

    @property
    def count(self) -> int:
        return len(self.runs)

    @property
    def total_wall_seconds(self) -> float:
        return sum(r.wall_seconds for r in self.runs)

    @property
    def total_cpu_seconds(self) -> float:
        return sum(r.cpu_seconds for r in self.runs)

    @property
    def avg_wall_seconds(self) -> float:
        return self.total_wall_seconds / self.count if self.count else 0.0

    @property
    def avg_cpu_seconds(self) -> float:
        return self.total_cpu_seconds / self.count if self.count else 0.0

    @property
    def peak_rss_end_bytes(self) -> int:
        """Peak RSS observed at stop() time (not continuous sampling)."""
        return max((r.rss_end_bytes for r in self.runs), default=0)


class BenchmarkService:
    """
    A small service class to measure performance metrics during a run.
    """

    def __init__(self, *, model_path: str | None = None, project_path: str | None = None, scenario: str = 'original') -> None:

        self._proc = psutil.Process(os.getpid())

        self._model_path: str | None = None
        self._model_size_mb: float | None = None

        self._project_path: str | None = None
        self._project_size_gb: float | None = None
        self._os_size_gb: float | None = None
        self._total_disk_size_gb: float | None = None
        self._free_disk_size_gb: float | None = None

        # Timer states:
        # - _active_starts stores start snapshots for currently running timers
        # - _timers aggregates completed runs per timer name
        self._active_starts: dict[str, dict[str, Any]] = {}
        self._timers: dict[str, _TimerStats] = {}

        self.set_model_path(model_path)
        self.set_project_path(project_path)
        self.set_os_sizes()

        self._detections: list | None = None
        self._avg_total_confidence: float | None = None

        self._scenario = scenario


    ############################################################################ 
    # Storage
    ############################################################################

    ############################################################################ 
    # Flash storage
    ############################################################################
    @staticmethod
    def get_model_size(path: str) -> float:
        """Returns the model file size in MB."""
        size_bytes = os.path.getsize(path)
        return _bytes_to_mb(size_bytes)

    def set_model_path(self, path: str | None) -> None:
        """Stores the model path and caches its file size (MB) for the summary output."""
        if path is None:
            self._model_size_mb = None
            return

        self._model_path = path
        try:
            self._model_size_mb = self.get_model_size(path)
        except OSError:
            # If file is missing, we keep size as unknown.
            self._model_size_mb = None

    def get_project_size(self, path: str | None) -> float:
        """Returns the project directory size in MB."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return _bytes_to_gb(total_size)

    def set_project_path(self, path: str | None) -> None:
        """Stores the project path and caches its directory size (MB) for the summary output."""
        if path is None:
            self._project_size_gb = None
            return

        self._project_path = path
        try:
            self._project_size_gb = self.get_project_size(path)
        except OSError:
            # If file is missing, we keep size as unknown.
            self._project_size_gb = None

    def set_os_sizes(self) -> None:
        """Sets the OS and total disk directory sizes in MB."""
        usage = shutil.disk_usage("/")

        self._os_size_gb = _bytes_to_gb(usage.used)
        self._total_disk_size_gb = _bytes_to_gb(usage.total)      
        self._free_disk_size_gb = _bytes_to_gb(usage.free)  

    ############################################################################ 
    # RAM Storage
    ############################################################################
    def _get_ram_usage_edge(self) -> float:
        """
        Uses unix system files
        """
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if "VmRSS" in line:
                        kb = int(line.split()[1])
                        return kb / 1024
        except Exception:
            return 0.0
        return 0.0

    def get_ram_usage_mb(self) -> float:
        """
        Current RAM usage (RSS: Resident Set Size) of the current Python process in MB.
        """
        return _bytes_to_mb(self._proc.memory_info().rss)

    def get_cpu_usage_percent(self, *, interval_s: float = 0.1) -> float:
        """
        Returns process CPU usage percent (normalized to 0..100 across all cores).

        Notes:
        - This uses psutil's sampling over a short interval.
        - Good for "current CPU usage now", not for measuring a specific block.
        """ 
        # psutil returns a percent that can exceed 100 on multi-core, has to be normalized
        raw = self._proc.cpu_percent(interval=interval_s)
        cores = psutil.cpu_count(logical=True) or 1
        return raw / cores

    def get_peak_ram_usage_mb(self) -> float:
        """
        Gets the maximum memory usage
        """
        if os.name == 'posix':  # Linux/Mac
            import resource
            # ru_maxrss in KB
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        return 0.0


    ############################################################################ 
    # Latency
    ############################################################################
    def start_timer(self, name: str) -> None:
        """
        Start a named timer.

        Supports:
        - Extended mode (psutil)
        - Light mode (os.times, no psutil)
        """
        if name in self._active_starts:
            raise ValueError(f"Timer '{name}' is already running. Stop it before starting again.")

        t0 = time.perf_counter() # wall time: real world time

        cpu_times = self._proc.cpu_times() # cpu time: real time value, the process was acitve 
        cpu0 = float(cpu_times.user + cpu_times.system)
        rss0 = int(self._proc.memory_info().rss)

        # Start runner to measure ram peaks during inference
        sampler = None
        if name == "inference":
            sampler = MemorySampler(self)
            sampler.start()

        self._active_starts[name] = {
            "t0": t0,
            "cpu0": cpu0,
            "rss0": rss0,
            "sampler": sampler
        }

    def stop_timer(self, name: str) -> float:
        """
        Stop a named timer and record its measurements.

        Works in both extended and light mode.
        """
        snap = self._active_starts.pop(name, None)
        if snap is None:
            raise ValueError(f"Timer '{name}' was not started.")

        t1 = time.perf_counter()

        cpu_times = self._proc.cpu_times()
        cpu1 = float(cpu_times.user + cpu_times.system)
        rss1 = int(self._proc.memory_info().rss)
            

        wall = max(0.0, t1 - float(snap["t0"]))
        cpu = max(0.0, cpu1 - float(snap["cpu0"]))

        # stop inference ram measure runner
        interval_peak_mb = 0.0
        if "sampler" in snap and snap["sampler"] is not None:
            interval_peak_mb = snap["sampler"].stop()
            snap["sampler"].join()

        run = _TimerRun(
            wall_seconds=wall,
            cpu_seconds=cpu,
            rss_start_bytes=int(snap["rss0"]),
            rss_end_bytes=rss1,
            peak_interval_mb=interval_peak_mb
        )

        stats = self._timers.setdefault(name, _TimerStats())
        stats.add_run(run)

        return wall

    def get_timer_stats(self, name: str) -> dict[str, float]:
        """
        Convenience method to read aggregated stats for a timer.

        Returns a dict with:
        - count
        - total_wall_s, avg_wall_s
        - total_cpu_s, avg_cpu_s
        - cpu_util_percent (normalized 0..100 across all cores; based on CPU-time / wall-time)
        """
        stats = self._timers.get(name, _TimerStats())
        cpu_util = 0.0

        cores = psutil.cpu_count(logical=True) or 1

        if stats.total_wall_seconds > 0:
            # CPU utilization for the block:
            # (CPU seconds / wall seconds) gives "fraction of one core".
            # Divide by core count to normalize to 0..100 for the whole machine.
            cpu_util = (stats.total_cpu_seconds / stats.total_wall_seconds) * 100.0 / cores

        return {
            "count": float(stats.count),
            "total_wall_s": float(stats.total_wall_seconds),
            "avg_wall_s": float(stats.avg_wall_seconds),
            "total_cpu_s": float(stats.total_cpu_seconds),
            "avg_cpu_s": float(stats.avg_cpu_seconds),
            "cpu_util_percent": float(cpu_util),
        }

    ############################################################################ 
    # Accuracy
    ############################################################################
    def set_detections(self, detections: Any) -> None:
        """Calculates and stores the average confidence and all detections"""
        if not detections:
            return

        total_conf = 0.0
        count = 0
        detections_list = []
        for pred in detections:
            confidence = pred.confidence if hasattr(pred, "confidence") else pred.get("confidence", 0.0)
            scientific_name = pred.scientific_name if hasattr(pred, "scientific_name") else pred.get("scientific_name", "Unknown")

            if confidence is None or scientific_name is None:
                continue

            total_conf += confidence
            count += 1

            detections_list.append({
                "confidence": confidence,
                "scientific_name": scientific_name
            })

        self._avg_total_confidence = total_conf / count if count > 0 else None        
        self._detections = detections_list


    ############################################################################ 
    # Logging and output
    ############################################################################
    # def write_to_csv_log(self, file_path: str = "ownTests/performance/metrics_log.csv") -> None:
    #     """
    #     Writes the current metrics into a CSV file (appends one row per run).
    #     """
    #     # Prepare timestamp
    #     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #     # Get values (safe defaults if not available)
    #     model_size = f"{self._model_size_mb:.2f}" if self._model_size_mb is not None else "NA"

    #     confidence = f"{self._confidence * 100:.2f}" if self._confidence is not None else "NA"
    #     ram_usage = f"{self.get_ram_usage_mb():.2f}"
    #     peak_ram_usage = f"{self.get_peak_ram_usage_mb():.2f}"

    #     # Helper to extract timer values
    #     def get_avg_time(timer_name: str) -> str:
    #         if timer_name not in self._timers:
    #             return "NA"
    #         stats = self.get_timer_stats(timer_name)
    #         return f"{stats['avg_wall_s']:.4f}"

    #     model_load_time = get_avg_time("model_load")
    #     audio_time = get_avg_time("audio_processing")
    #     inference_time = get_avg_time("inference")

    #     # Get peak ram usage during inference
    #     inference_peak = "NA"
    #     if "inference" in self._timers:
    #         # Wir nehmen den höchsten Peak-Wert aller bisherigen Inferenz-Runs
    #         runs = self._timers["inference"].runs
    #         inference_peak = f"{max((r.peak_interval_mb for r in runs), default=0.0):.2f}"

    #     # CSV header
    #     header = (
    #         "Timestamp,Scenario,Model Size (MB),Average Confidence (%),"
    #         "RAM Usage (MB), Total Peak RAM Usage (MB), Inference Peak RAM Usage (MB), Model Load Time (s),Audio Processing Time (s),"
    #         "Inference Time (s)\n"
    #     )

    #     # CSV row
    #     row = (
    #         f"{timestamp},{self._scenario},{model_size},{confidence},"
    #         f"{ram_usage}, {peak_ram_usage}, {inference_peak},{model_load_time},{audio_time},{inference_time}\n"
    #     )

    #     # Make directory if it doesn't exist
    #     os.makedirs(os.path.dirname(file_path), exist_ok=True)

    #     # Check if file exists
    #     file_exists = os.path.isfile(file_path)

    #     # Write to file
    #     with open(file_path, "a") as f:
    #         if not file_exists:
    #             f.write(header)
    #         f.write(row)

    def print_summary(self) -> None:
        """Print all collected metrics in a structured, beginner-friendly format."""
        ram_now_mb = self.get_ram_usage_mb()
        peak_ram_usage = self.get_peak_ram_usage_mb()

        print(f"\n===PERFORMANCE METRICS===")
        print("Scenario: ", self._scenario)
        print("Timestamp: ", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        print("")
        print("==STORAGE==")
        print("=FLASH STORAGE=")
        if self._total_disk_size_gb is not None:
            print(f"Total Disk Size: {self._total_disk_size_gb:.2f} GB")
        elif self._total_disk_size_gb is None:
            print("Total Disk Size: (unknown)")

        if self._os_size_gb is not None:
            print(f"OS Disk Size: {self._os_size_gb:.2f} GB")
        elif self._os_size_gb is None:
            print("OS Disk Size: (unknown)")

        if self._project_size_gb is not None:
            print(f"Project Size: {self._project_size_gb:.2f} GB")
        elif self._project_path:
            print("Project Size: (unknown - file not found)")

        if self._model_size_mb is not None:
            print(f"Model Size: {self._model_size_mb:.2f} MB")
        elif self._model_path:
            print("Model Size: (unknown - file not found)")
        else:
            print("Model Size: (not set)")
        
        if self._free_disk_size_gb is not None:
            print(f"Free Disk Size: {self._free_disk_size_gb:.2f} GB ({(self._free_disk_size_gb / self._total_disk_size_gb * 100.0) if self._total_disk_size_gb else 0.0:.1f} %)")
        elif self._free_disk_size_gb is None:
            print("Free Disk Size: (unknown)")

        print("")
        print("=RAM USAGE=")
        print(f"RAM Usage (current RSS): {ram_now_mb:.2f} MB")
        print(f"Peak RAM Usage: {peak_ram_usage:.2f} MB")

        print("")
        print("==ACCURACY==")
        print(f"Total Average Confidence: {(self._avg_total_confidence * 100.0):.2f} %" if self._avg_total_confidence is not None else "Average Confidence: (unknown)")
        print("Detections:")
        if self._detections is not None:
            for det in self._detections:
                conf = det.get("confidence", 0.0)
                sci_name = det.get("scientific_name", "Unknown")
                print(f" - {sci_name}: {conf * 100:.2f} % confidence")
        else:
            print(f"Detections: {len(self._detections)}" if self._detections is not None else "Detections: (unknown)")

        # Common timers
        print("")
        print("==LATENCIES==")
        for label, timer_name in (
            ("Model Load Time", "model_load"),
            ("Audio Processing Time", "audio_processing"),
            ("Inference Time", "inference"),
        ):
            if timer_name not in self._timers:
                continue
            stats = self.get_timer_stats(timer_name)
            avg = stats["avg_wall_s"]
            total = stats["total_wall_s"]
            n = int(stats["count"])
            cpu_util = stats["cpu_util_percent"]

            if n <= 1:
                print(f"{label}: {total:.4f} s (CPU util ~ {cpu_util:.1f} %)")
            else:
                print(f"{label}: {total:.4f} s total | {avg:.4f} s avg (n={n}) (CPU util ~ {cpu_util:.1f} %)")

        # If there are additional timers, print them too.
        extra = [k for k in self._timers.keys() if k not in {"model_load", "audio_processing", "inference"}]
        for name in sorted(extra):
            stats = self.get_timer_stats(name)
            n = int(stats["count"])
            if n <= 1:
                print(f"{name}: {stats['total_wall_s']:.4f} s")
            else:
                print(f"{name}: {stats['total_wall_s']:.4f} s total | {stats['avg_wall_s']:.4f} s avg (n={n})")

        print("===========================\n")

