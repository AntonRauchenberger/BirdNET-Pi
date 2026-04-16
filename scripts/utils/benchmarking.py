"""
Reusable monitoring / benchmarking utilities for BirdNET-Pi

Main features:
- Multiple timers at the same time (by name)
- Process RAM usage (RSS) and curve over time
- Confidence during prediction
- Flash storage calculations
- Log results to CSV files
"""

from __future__ import annotations

import os
import time
import datetime
import threading
import psutil
from dataclasses import dataclass, field
from typing import Any
import shutil
from .constants import BenchmarkTimerNames

# Binary size units are used (1024 instead of 1000)
def _bytes_to_mb(num_bytes: float) -> float:
    return num_bytes / (1024 * 1024)

def _bytes_to_gb(num_bytes: float) -> float:
    return num_bytes / (1024 * 1024 * 1024)

class _PerformanceSampler(threading.Thread):
    def __init__(self, service_ref: "BenchmarkService", interval_s: float = 0.1):
        super().__init__(daemon=True)
        self.service = service_ref
        self.interval_s = interval_s
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            timestamp = time.perf_counter()
            ram_mb = self.service.get_ram_usage_mb()
            cpu_percent = None
            if self.service._enable_cpu_metrics:
                cpu_percent = self.service.get_cpu_usage_percent(interval_s=0.0)
            self.service._record_performance_sample(timestamp, ram_mb, cpu_percent)
            time.sleep(self.interval_s)

    def stop(self) -> None:
        self._stop_event.set()

@dataclass
class _TimerRun:
    """Stores raw data for one timer run (start -> stop)."""

    wall_seconds: float
    cpu_seconds: float
    rss_start_bytes: int # Needed RAM storage at the start
    rss_end_bytes: int

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

    def __init__(self, *, model_path: str | None = None, project_path: str | None = None, scenario: str = 'original', sample_interval_s: float = 0.1, enable_cpu_metrics: bool = False, idle_history_s: float = 20.0, idle_max_samples: int = 500, results_dir: str | None = None) -> None:

        self._proc = psutil.Process(os.getpid())

        self._model_path: str | None = None
        self._model_size_mb: float | None = None

        self._project_path: str | None = None
        self._project_size_gb: float | None = None
        self._os_size_gb: float | None = None
        self._total_disk_size_gb: float | None = None
        self._free_disk_size_gb: float | None = None
        self._total_ram_mb: float | None = None

        # Timer states:
        # - _active_starts stores start snapshots for currently running timers
        # - _timers aggregates completed runs per timer name
        self._active_starts: dict[str, dict[str, Any]] = {}
        self._timers: dict[str, _TimerStats] = {}

        self.set_model_path(model_path)
        self.set_project_path(project_path)
        self.set_os_sizes()
        self.set_total_ram_size_mb()

        self._detections: list | None = None
        self._avg_total_confidence: float | None = None

        self._scenario = scenario

        self._sample_interval_s = sample_interval_s
        self._enable_cpu_metrics = enable_cpu_metrics
        self._idle_history_s = idle_history_s
        self._idle_max_samples = idle_max_samples
        self._measurement_lock = threading.Lock()
        self._performance_samples: dict[str, list[dict[str, Any]]] = {
            "idle": [],
            "analysis": []
        }
        self._performance_curve: list[dict[str, Any]] = []
        self._current_phase = "idle"
        self._start_time = time.perf_counter()

        if self._enable_cpu_metrics:
            self._proc.cpu_percent(interval=None)

        self._performance_sampler = _PerformanceSampler(self, self._sample_interval_s)
        self._performance_sampler.start()
        self._record_performance_sample(
            self._start_time,
            self.get_ram_usage_mb(),
            self.get_cpu_usage_percent(interval_s=0.0) if self._enable_cpu_metrics else None,
        )

        self._results_dir: str | None = None
        self._results_log_dir: str | None = None
        self._results_curves_dir: str | None = None
        self.set_results_dirs(results_dir)
        self.write_csv_header()


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
    # PERFORMANCE (RAM, CPU)
    ############################################################################
    def set_total_ram_size_mb(self):
        """Total RAM size of the machine in MB."""
        self._total_ram_mb = _bytes_to_mb(psutil.virtual_memory().total)

    def get_ram_usage_mb(self) -> float:
        """
        Current RAM usage (RSS: Resident Set Size) of the current Python process in MB.
        """
        return _bytes_to_mb(self._proc.memory_info().rss)

    def get_cpu_usage_percent(self, *, interval_s: float | None = 0.1) -> float:
        """
        Returns process CPU usage percent (normalized to 0..100 across all cores).

        Notes:
        - If interval_s is 0 or None, psutil returns a non-blocking value based on the previous call.
        - Good for lightweight sampling in a background collector thread.
        """
        if interval_s is None or interval_s == 0.0:
            raw = self._proc.cpu_percent(interval=None)
        else:
            raw = self._proc.cpu_percent(interval=interval_s)
        cores = psutil.cpu_count(logical=True) or 1
        return raw / cores

    def _record_performance_sample(self, timestamp: float, ram_mb: float, cpu_percent: float | None = None) -> None:
        sample = {
            "timestamp_s": timestamp - self._start_time,
            "ram_mb": ram_mb,
            "phase": self._current_phase
        }
        if cpu_percent is not None:
            sample["cpu_percent"] = cpu_percent

        with self._measurement_lock:
            samples = self._performance_samples.setdefault(self._current_phase, [])
            samples.append(sample)
            if self._current_phase == "idle":
                cutoff = sample["timestamp_s"] - self._idle_history_s
                if cutoff > 0 or len(samples) > self._idle_max_samples:
                    keep_index = 0
                    while keep_index < len(samples) and samples[keep_index]["timestamp_s"] < cutoff:
                        keep_index += 1
                    if keep_index:
                        del samples[:keep_index]
                    if len(samples) > self._idle_max_samples:
                        del samples[:-self._idle_max_samples]
    
    def build_performance_curve(self):
        """Combines idle and analysis performance samples into a single sorted timeline."""
        with self._measurement_lock:
            combined = self._performance_samples.get("idle", []) + self._performance_samples.get("analysis", [])
            self._performance_curve = sorted(combined, key=lambda x: x["timestamp_s"])


    ############################################################################ 
    # Latency
    ############################################################################
    def start_timer(self, name: str) -> None:
        """
        Start a named timer.

        Supports:
        - Extended mode (psutil)
        - Light mode (os.times, no psutil)
        
        Note: Phase transitions must be managed separately via set_phase().
        """
        if name in self._active_starts:
            raise ValueError(f"Timer '{name}' is already running. Stop it before starting again.")

        t0 = time.perf_counter() # wall time: real world time

        cpu_times = self._proc.cpu_times() # cpu time: real time value, the process was acitve 
        cpu0 = float(cpu_times.user + cpu_times.system)
        rss0 = int(self._proc.memory_info().rss)

        self._active_starts[name] = {
            "t0": t0,
            "cpu0": cpu0,
            "rss0": rss0
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

        run = _TimerRun(
            wall_seconds=wall,
            cpu_seconds=cpu,
            rss_start_bytes=int(snap["rss0"]),
            rss_end_bytes=rss1
        )

        stats = self._timers.setdefault(name, _TimerStats())
        stats.add_run(run)

        return wall

    def set_phase(self, phase: str) -> None:
        """
        Switch active phase and record a performance sample immediately.
        
        This marks explicit phase transitions (idle <-> analysis) in the performance curve.
        """
        self._current_phase = phase
        timestamp = time.perf_counter()
        ram_mb = self.get_ram_usage_mb()
        cpu_percent = self.get_cpu_usage_percent(interval_s=0.0) if self._enable_cpu_metrics else None
        self._record_performance_sample(timestamp, ram_mb, cpu_percent)

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
    def do_final_calculations(self):
        self.build_performance_curve()

    def reset_data(self):
        """Resets all collected data. Useful for multiple runs in the same process."""
        self._active_starts.clear()
        self._timers.clear()
        self._performance_samples = {"idle": [], "analysis": []}
        self._performance_curve = []
        self._current_phase = "idle"
        self._start_time = time.perf_counter()
        self._detections = None
        self._avg_total_confidence = None

    def set_results_dirs(self, path: str | None) -> None:
        """Sets the directories where results will be saved."""
        if path is not None:
            results_base_path = os.path.join(path, self._scenario)
            log_dir = os.path.join(results_base_path)
            curves_dir = os.path.join(results_base_path, "curves")

            os.makedirs(results_base_path, exist_ok=True)
            os.makedirs(log_dir, exist_ok=True)
            os.makedirs(curves_dir, exist_ok=True)

            self._results_dir = results_base_path
            self._results_log_dir = log_dir
            self._results_curves_dir = curves_dir

    def write_csv_header(self):
        """Writes the header to the log CSV file, including storage info and column names."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Format storage values as strings
        total_disk_size = f"{self._total_disk_size_gb:.2f}" if self._total_disk_size_gb is not None else "NA"
        os_disk_size = f"{self._os_size_gb:.2f}" if self._os_size_gb is not None else "NA"
        project_size = f"{self._project_size_gb:.2f}" if self._project_size_gb is not None else "NA"
        model_size = f"{self._model_size_mb:.2f}" if self._model_size_mb is not None else "NA"
        free_disk_size = f"{self._free_disk_size_gb:.2f}" if self._free_disk_size_gb is not None else "NA"
        total_ram_size = f"{self._total_ram_mb:.2f}" if self._total_ram_mb is not None else "NA"

        log_header = (
            "Scenario: " + self._scenario + ", Created: " + timestamp + "\n\n" +
            "Storage:\n" +
            "Total Disk Size (GB): " + total_disk_size + "\n" +
            "OS Disk Size (GB): " + os_disk_size + "\n" +
            "Project Size (GB): " + project_size + "\n" +
            "Model Size (MB): " + model_size + "\n" +
            "Free Disk Size (GB): " + free_disk_size + "\n" +
            "Total RAM Size (MB): " + total_ram_size + "\n\n" +
            "Timestamp, Avg Confidence (%),Detections,Total Analysis (s),Inference (s),Model Load (s),Audio Processing (s),Total Reporting (s)\n"
        )

        if not os.path.exists(os.path.join(self._results_log_dir, "metrics_log.csv")):
            with open(os.path.join(self._results_log_dir, "metrics_log.csv"), "w") as log_file:
                log_file.write(log_header)

    def log_results_to_csv(self):
        """Writes performance metrics to log CSV and performance curves to curves CSV."""
        if self._results_log_dir is None or self._results_curves_dir is None:
            return
        
        self.do_final_calculations()
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write performance curve to curves file
        curve_file = os.path.join(self._results_curves_dir, f"{timestamp}_performance_curve.csv")
        curves_header = "timestamp_s,phase,ram_mb,cpu_percent\n"
        with open(curve_file, "w") as curves_file:
            curves_file.write(curves_header)
            for sample in self._performance_curve:
                timestamp_s = sample["timestamp_s"]
                phase = sample["phase"]
                ram_mb = sample["ram_mb"]
                cpu_percent = sample.get("cpu_percent", "")
                rounded_cpu_percent = f"{float(cpu_percent):.2f}" if cpu_percent else "0.00"
                curves_file.write(f"{timestamp_s:.4f},{phase},{ram_mb:.2f},{rounded_cpu_percent}\n")
        
        # Gather timer statistics
        total_analysis_time = 0.0
        inference_time = 0.0
        model_load_time = 0.0
        audio_processing_time = 0.0
        total_reporting_time = 0.0
        
        if BenchmarkTimerNames.TOTAL_ANALYSIS.value in self._timers:
            total_analysis_time = self.get_timer_stats(BenchmarkTimerNames.TOTAL_ANALYSIS.value)["total_wall_s"]
        if BenchmarkTimerNames.INFERENCE.value in self._timers:
            inference_time = self.get_timer_stats(BenchmarkTimerNames.INFERENCE.value)["total_wall_s"]
        if BenchmarkTimerNames.MODEL_LOADING.value in self._timers:
            model_load_time = self.get_timer_stats(BenchmarkTimerNames.MODEL_LOADING.value)["total_wall_s"]
        if BenchmarkTimerNames.AUDIO_PROCESSING.value in self._timers:
            audio_processing_time = self.get_timer_stats(BenchmarkTimerNames.AUDIO_PROCESSING.value)["total_wall_s"]
        if BenchmarkTimerNames.TOTAL_REPORTING.value in self._timers:
            total_reporting_time = self.get_timer_stats(BenchmarkTimerNames.TOTAL_REPORTING.value)["total_wall_s"]
        
        # Get accuracy metrics
        confidence = (self._avg_total_confidence * 100.0) if self._avg_total_confidence is not None else 0.0
        detections_count = len(self._detections) if self._detections is not None else 0
        
        # Build and write CSV row to log file
        row = (
            f"{timestamp},"
            f"{confidence:.2f},"
            f"{detections_count},"
            f"{total_analysis_time:.4f},"
            f"{inference_time:.4f},"
            f"{model_load_time:.4f},"
            f"{audio_processing_time:.4f},"
            f"{total_reporting_time:.4f}\n"
        )
        
        log_file = os.path.join(self._results_log_dir, "metrics_log.csv")
        with open(log_file, "a") as log_f:
            log_f.write(row)

        self.reset_data()

    def print_summary(self) -> None:
        """Print all collected metrics in a structured, beginner-friendly format."""
        self.do_final_calculations()

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
        print("=RAM STORAGE")
        if self._total_ram_mb is not None:
            print(f"Total RAM Size: {self._total_ram_mb:.2f} MB")
        elif self._total_ram_mb is None:
            print("Total RAM Size: (unknown)")

        print("")
        print("=RAM USAGE CURVE=")
        if self._performance_curve:
            for sample in self._performance_curve:
                timestamp = sample["timestamp_s"]
                ram_mb = sample["ram_mb"]
                cpu_percent = sample.get("cpu_percent")
                phase = sample.get("phase", "unknown")
                cpu_str = f", CPU: {cpu_percent:.1f} %" if cpu_percent is not None else ""
                print(f"Time: {timestamp:.2f} s, Phase: {phase}, RAM: {ram_mb:.2f} MB ({(ram_mb / self._total_ram_mb * 100.0) if self._total_ram_mb else 0.0:.1f} %) {cpu_str}")
        else:
            print("RAM usage curve: (no samples recorded)")

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
            (BenchmarkTimerNames.MODEL_LOADING.value, BenchmarkTimerNames.MODEL_LOADING.value),
            (BenchmarkTimerNames.AUDIO_PROCESSING.value, BenchmarkTimerNames.AUDIO_PROCESSING.value),
            (BenchmarkTimerNames.INFERENCE.value, BenchmarkTimerNames.INFERENCE.value),
        ):
            if timer_name not in self._timers:
                continue
            stats = self.get_timer_stats(timer_name)
            avg = stats["avg_wall_s"]
            total = stats["total_wall_s"]
            n = int(stats["count"])

            if n <= 1:
                print(f"{label}: {total:.4f} s")
            else:
                print(f"{label}: {total:.4f} s total | {avg:.4f} s avg (n={n})")

        # If there are additional timers, print them too.
        extra = [k for k in self._timers.keys() if k not in {BenchmarkTimerNames.MODEL_LOADING.value, BenchmarkTimerNames.AUDIO_PROCESSING.value, BenchmarkTimerNames.INFERENCE.value}]
        for name in sorted(extra):
            stats = self.get_timer_stats(name)
            n = int(stats["count"])
            if n <= 1:
                print(f"{name}: {stats['total_wall_s']:.4f} s")
            else:
                print(f"{name}: {stats['total_wall_s']:.4f} s total | {stats['avg_wall_s']:.4f} s avg (n={n})")

        print("===========================\n")

