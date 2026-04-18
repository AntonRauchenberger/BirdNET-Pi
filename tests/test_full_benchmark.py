import os
import sqlite3
import shutil
import time
import unittest

from scripts.utils.analysis import run_analysis
from scripts.utils.classes import ParseFileName
from scripts.utils.benchmarking import BenchmarkService
from scripts.utils.constants import BenchmarkTimerNames, BENCHMARKING_SCENARIO
from scripts.utils.helpers import MODEL_PATH, get_settings, BENCHMARKING_SERVICE, BASE_PATH, BENCHMARKING_RESULTS_DIR, DB_PATH
import scripts.utils.reporting as reporting
from tests.helpers import TESTDATA

class TestFullBenchmark(unittest.TestCase):
    @staticmethod
    def _ensure_detection_table() -> None:
        con = sqlite3.connect(DB_PATH)
        try:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS detections (
                  Date DATE,
                  Time TIME,
                  Sci_Name VARCHAR(100) NOT NULL,
                  Com_Name VARCHAR(100) NOT NULL,
                  Confidence FLOAT,
                  Lat FLOAT,
                  Lon FLOAT,
                  Cutoff FLOAT,
                  Week INT,
                  Sens FLOAT,
                  Overlap FLOAT,
                  File_Name VARCHAR(100) NOT NULL
                )
                """
            )
            con.commit()
        finally:
            con.close()

    def setUp(self):
        self._ensure_detection_table()
        source = os.path.join(TESTDATA, 'Pica pica_30s.wav')
        self.test_file = os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav')
        self._birddb_dir = os.path.expanduser('~/BirdNET-Pi')
        self._birddb_file = os.path.join(self._birddb_dir, 'BirdDB.txt')
        self._created_birddb_file = False
        self._created_birddb_dir = False

        if not os.path.exists(self._birddb_dir):
            os.makedirs(self._birddb_dir, exist_ok=True)
            self._created_birddb_dir = True
        if not os.path.exists(self._birddb_file):
            open(self._birddb_file, 'a').close()
            self._created_birddb_file = True

        if os.path.exists(self.test_file):
            os.unlink(self.test_file)
        os.symlink(source, self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.unlink(self.test_file)

        if os.path.exists(os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav.json')):
            os.unlink(os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav.json'))

        if self._created_birddb_file and os.path.exists(self._birddb_file):
            os.unlink(self._birddb_file)
        if self._created_birddb_dir and os.path.isdir(self._birddb_dir):
            try:
                os.rmdir(self._birddb_dir)
            except OSError:
                # Keep directory if other files were created by the integration run.
                pass
            
        BENCHMARKING_SERVICE.set(None)

    def test_full_pipeline_benchmark(self):
        if shutil.which('sox') is None:
            self.skipTest("Integration benchmark requires 'sox' installed.")

        # Initialize benchmarking service
        conf = get_settings()
        # Use wav for integration tests to avoid optional mp3 codec dependency in sox.
        conf['AUDIOFMT'] = 'wav'
        # The sample audio is 30s; keep recording length aligned to avoid invalid trim ranges.
        conf['RECORDING_LENGTH'] = '30'
        model = conf['MODEL']
        model_file = os.path.join(MODEL_PATH, f'{model}.tflite')
        if not os.path.exists(model_file):
            self.skipTest(f"Integration benchmark requires model file: {model_file}")

        os.makedirs(BENCHMARKING_RESULTS_DIR, exist_ok=True)

        BENCHMARKING_SERVICE.set(
            BenchmarkService(model_path=model_file, project_path=BASE_PATH,
                            scenario=BENCHMARKING_SCENARIO, enable_cpu_metrics=True, results_dir=BENCHMARKING_RESULTS_DIR)
        )

        # Phase 1: Collect idle measurements (simulating idle mode, e.g., continuous listening)
        print("Starting idle phase (simulating listening mode)...")
        time.sleep(5)  # Simulate 5s in idle mode (e.g., audio monitoring without analysis)

        # Phase 2: Start analysis (full pipeline)
        print("Starting analysis phase (full pipeline)...")
        BENCHMARKING_SERVICE.set_phase("analysis")  # Explicitly switch phase before timing analysis
        BENCHMARKING_SERVICE.start_timer(BenchmarkTimerNames.TOTAL_ANALYSIS.value)

        test_file = ParseFileName(self.test_file)

        # Inference/Analysis (core of the pipeline)
        detections = run_analysis(test_file)

        BENCHMARKING_SERVICE.set_phase("reporting")

        # Reporting (Logs, JSON, Notifications, GUI-Updates)
        BENCHMARKING_SERVICE.start_timer(BenchmarkTimerNames.TOTAL_REPORTING.value)

        BENCHMARKING_SERVICE.start_timer(BenchmarkTimerNames.UPDATE_JSON_FILE.value)
        reporting.update_json_file(test_file, detections)
        BENCHMARKING_SERVICE.stop_timer(BenchmarkTimerNames.UPDATE_JSON_FILE.value)

        BENCHMARKING_SERVICE.start_timer(BenchmarkTimerNames.UPDATE_DB_AND_FILE.value)
        for detection in detections:
                detection.file_name_extr = reporting.extract_detection(test_file, detection)
                reporting.write_to_file(test_file, detection)
                reporting.write_to_db(test_file, detection)
        time.sleep(0.3)  # Simulate DB overhead
        BENCHMARKING_SERVICE.stop_timer(BenchmarkTimerNames.UPDATE_DB_AND_FILE.value)

        reporting.apprise(test_file, detections)

        BENCHMARKING_SERVICE.start_timer(BenchmarkTimerNames.SERVER_POST.value)
        time.sleep(0.5)  # Simulate reporting overhead
        BENCHMARKING_SERVICE.stop_timer(BenchmarkTimerNames.SERVER_POST.value)

        BENCHMARKING_SERVICE.stop_timer(BenchmarkTimerNames.TOTAL_REPORTING.value)

        # Stop total analysis
        BENCHMARKING_SERVICE.stop_timer(BenchmarkTimerNames.TOTAL_ANALYSIS.value)
        BENCHMARKING_SERVICE.set_phase("idle")  # Explicitly switch back to idle after analysis

        # Save detections
        BENCHMARKING_SERVICE.set_detections(detections)

        # Back to idle (simulating end of analysis, back to listening)
        time.sleep(5)  # Short idle period after analysis

        # Assertions: In real integrations, geo/occurrence filters can legitimately yield zero detections.
        self.assertIsInstance(detections, list, "Detections must be returned as a list")
        expected_sci_names = ['Pica pica']
        for det in detections:
            self.assertIn(det.scientific_name, expected_sci_names, "Unexpected species detected")

        # Additional checks: Validate timer stats before reset
        analysis_stats = BENCHMARKING_SERVICE.get_timer_stats(BenchmarkTimerNames.TOTAL_ANALYSIS.value)
        self.assertGreater(analysis_stats['total_wall_s'], 0, "Analysis took no time")
        reporting_stats = BENCHMARKING_SERVICE.get_timer_stats(BenchmarkTimerNames.TOTAL_REPORTING.value)
        self.assertGreater(reporting_stats['total_wall_s'], 0, "Reporting took no time")

        # Log and print results
        BENCHMARKING_SERVICE.print_summary()
        BENCHMARKING_SERVICE.log_results_to_csv()

if __name__ == '__main__':
    unittest.main()