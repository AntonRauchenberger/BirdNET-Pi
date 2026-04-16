import os
import unittest
from unittest.mock import patch

from scripts.utils.analysis import run_analysis
from scripts.utils.classes import ParseFileName
from tests.helpers import TESTDATA, Settings
from scripts.utils.helpers import MODEL_PATH, get_settings, BENCHMARKING_SERVICE, BASE_PATH

from scripts.utils.benchmarking import BenchmarkService

class TestRunAnalysis(unittest.TestCase):

    def setUp(self):
        source = os.path.join(TESTDATA, 'Pica pica_30s.wav')
        self.test_file = os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav')
        if os.path.exists(self.test_file):
            os.unlink(self.test_file)
        os.symlink(source, self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.unlink(self.test_file)

        BENCHMARKING_SERVICE.set(None)

    @patch('scripts.utils.helpers._load_settings')
    @patch('scripts.utils.analysis.loadCustomSpeciesList')
    def test_run_analysis(self, mock_loadCustomSpeciesList, mock_load_settings):
        # Mock the settings and species list
        mock_load_settings.return_value = Settings.with_defaults()
        mock_loadCustomSpeciesList.return_value = []

        # Initialize benchmarking service
        conf = get_settings()
        model = conf['MODEL']
        BENCHMARKING_SERVICE.set(
            BenchmarkService(model_path=os.path.join(MODEL_PATH, f'{model}.tflite'), project_path=BASE_PATH,
                            scenario="Local Laptop", enable_cpu_metrics=True)
        )
        # Test file
        test_file = ParseFileName(self.test_file)

        # Expected results
        expected_results = [
            {"confidence": 0.912, 'sci_name': 'Pica pica'},
            {"confidence": 0.9316, 'sci_name': 'Pica pica'},
            {"confidence": 0.8857, 'sci_name': 'Pica pica'}
        ]

        # Start analysis timer
        BENCHMARKING_SERVICE.start_timer("total analysis")

        # Run the analysis
        detections = run_analysis(test_file)

        # Stop analysis timer
        BENCHMARKING_SERVICE.stop_timer("total analysis")

        # Save detections
        BENCHMARKING_SERVICE.set_detections(detections)
    
        # TODO Log benchmark results
        BENCHMARKING_SERVICE.print_summary()

        # Assertions
        self.assertEqual(len(detections), len(expected_results))
        for det, expected in zip(detections, expected_results):
            self.assertAlmostEqual(det.confidence, expected['confidence'], delta=1e-4)
            self.assertEqual(det.scientific_name, expected['sci_name'])

if __name__ == '__main__':
    unittest.main()
