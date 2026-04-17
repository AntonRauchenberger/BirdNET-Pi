import os
import time
import unittest
from unittest.mock import patch, MagicMock

from scripts.utils.analysis import run_analysis
from scripts.utils.classes import ParseFileName
from scripts.utils.benchmarking import BenchmarkService
from scripts.utils.constants import BenchmarkTimerNames, BENCHMARKING_SCENARIO
from scripts.utils.helpers import MODEL_PATH, get_settings, BENCHMARKING_SERVICE, BASE_PATH, BENCHMARKING_RESULTS_DIR
import scripts.utils.reporting as reporting
from tests.helpers import TESTDATA, Settings

class TestFullBenchmark(unittest.TestCase):
    def setUp(self):
        source = os.path.join(TESTDATA, 'Pica pica_30s.wav')
        self.test_file = os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav')
        if os.path.exists(self.test_file):
            os.unlink(self.test_file)
        os.symlink(source, self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.unlink(self.test_file)

        if os.path.exists(os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav.json')):
            os.unlink(os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav.json'))
            
        BENCHMARKING_SERVICE.set(None)

    @patch('scripts.utils.reporting.write_to_file')
    @patch('scripts.utils.reporting.spectrogram')
    @patch('scripts.utils.reporting.extract_safe')
    @patch('scripts.utils.reporting.get_settings')
    @patch('scripts.utils.reporting.apprise')
    @patch('scripts.utils.reporting.write_to_db')
    @patch('scripts.utils.analysis.loadCustomSpeciesList')
    @patch('scripts.utils.helpers._load_settings')
    def test_full_pipeline_benchmark(self, mock_load_settings, mock_loadCustomSpeciesList, mock_write_to_db, mock_apprise, mock_reporting_get_settings, mock_extract_safe, mock_spectrogram, mock_write_to_file):
        # Mock settings and species list
        mock_load_settings.return_value = Settings.with_defaults()
        mock_loadCustomSpeciesList.return_value = []
        mock_extract_safe.return_value = None
        mock_spectrogram.return_value = None
        mock_write_to_file.return_value = None

        # Mock Reporting configuration to allow write_to_json_file to work
        report_conf = Settings.with_defaults()
        report_conf['RECORDING_LENGTH'] = 30
        report_conf['BIRDWEATHER_ID'] = ''
        report_conf['AUDIOFMT'] = 'wav'
        report_conf['EXTRACTED'] = '/tmp/extracted'
        report_conf['RAW_SPECTROGRAM'] = 0
        mock_reporting_get_settings.return_value = report_conf

        # Mock DB- and Apprise-Calls
        mock_write_to_db.return_value = None
        mock_apprise.return_value = None

        # Initialize benchmarking service
        conf = get_settings()
        model = conf['MODEL']
        BENCHMARKING_SERVICE.set(
            BenchmarkService(model_path=os.path.join(MODEL_PATH, f'{model}.tflite'), project_path=BASE_PATH,
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

        # Assertions: Check if the pipeline was successful
        self.assertGreater(len(detections), 0, "No detections found – pipeline failed")
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

        # Mock verifications: Ensure DB and notifications were simulated
        mock_write_to_db.assert_called()
        mock_apprise.assert_called()

if __name__ == '__main__':
    unittest.main()