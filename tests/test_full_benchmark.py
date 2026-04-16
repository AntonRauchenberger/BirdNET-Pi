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
        # Testdaten vorbereiten (wie im ursprünglichen Test: Symlink mit Datum im Namen erstellen)
        source = os.path.join(TESTDATA, 'Pica pica_30s.wav')
        self.test_file = os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav')  # Dateiname mit Datum für ParseFileName
        if os.path.exists(self.test_file):
            os.unlink(self.test_file)
        os.symlink(source, self.test_file)

    def tearDown(self):
        # Aufräumen
        if os.path.exists(self.test_file):
            os.unlink(self.test_file)

        if os.path.exists(os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav.json')):
            os.unlink(os.path.join(TESTDATA, '2024-02-24-birdnet-16:19:37.wav.json'))
            
        BENCHMARKING_SERVICE.set(None)

    @patch('scripts.utils.reporting.get_settings')
    @patch('scripts.utils.reporting.apprise')
    @patch('scripts.utils.reporting.write_to_db')
    @patch('scripts.utils.analysis.loadCustomSpeciesList')
    @patch('scripts.utils.helpers._load_settings')
    def test_full_pipeline_benchmark(self, mock_load_settings, mock_loadCustomSpeciesList, mock_write_to_db, mock_apprise, mock_reporting_get_settings):
        # Mock Settings und Species-Liste
        mock_load_settings.return_value = Settings.with_defaults()
        mock_loadCustomSpeciesList.return_value = []

        # Mock Reporting-Konfiguration, damit write_to_json_file funktionieren kann
        report_conf = Settings.with_defaults()
        report_conf['RECORDING_LENGTH'] = 30
        report_conf['BIRDWEATHER_ID'] = ''
        mock_reporting_get_settings.return_value = report_conf

        # Mock DB- und Apprise-Aufrufe
        mock_write_to_db.return_value = None
        mock_apprise.return_value = None

        # Benchmarking-Service initialisieren (nach Mocks)
        conf = get_settings()
        model = conf['MODEL']
        BENCHMARKING_SERVICE.set(
            BenchmarkService(model_path=os.path.join(MODEL_PATH, f'{model}.tflite'), project_path=BASE_PATH,
                            scenario=BENCHMARKING_SCENARIO, enable_cpu_metrics=True, results_dir=BENCHMARKING_RESULTS_DIR)
        )

        # Phase 1: Idle-Messungen sammeln (simuliert Ruhe-Modus, z. B. kontinuierliches Hören)
        print("Starting idle phase (simulating listening mode)...")
        time.sleep(5)  # Simuliert 5s im Ruhe-Modus (z. B. Audio-Überwachung ohne Analyse)

        # Phase 2: Analyse starten (gesamte Pipeline)
        print("Starting analysis phase (full pipeline)...")
        BENCHMARKING_SERVICE.set_phase("analysis")  # Explicitly switch phase before timing analysis
        BENCHMARKING_SERVICE.start_timer(BenchmarkTimerNames.TOTAL_ANALYSIS.value)

        test_file = ParseFileName(self.test_file)

        # Inferenz/Analyse (Kern der Pipeline)
        # run_analysis() startet intern bereits den INFERENCE-Timer, daher hier nicht doppelt starten.
        detections = run_analysis(test_file)

        # DB-Speicherung (simuliert Datenbank-Operationen)
        BENCHMARKING_SERVICE.start_timer(BenchmarkTimerNames.TOTAL_REPORTING.value)
        for det in detections:
            reporting.write_to_db(test_file, det)
        time.sleep(0.3)  # Simuliere DB-Overhead

        # Reporting (Logs, JSON, Notifications, GUI-Updates)
        reporting.write_to_json_file(test_file, detections)
        reporting.apprise(test_file, detections)
        time.sleep(0.5)  # Simuliere Reporting-Overhead
        BENCHMARKING_SERVICE.stop_timer(BenchmarkTimerNames.TOTAL_REPORTING.value)

        # Gesamt-Analyse stoppen
        BENCHMARKING_SERVICE.stop_timer(BenchmarkTimerNames.TOTAL_ANALYSIS.value)
        BENCHMARKING_SERVICE.set_phase("idle")  # Explicitly switch back to idle after analysis

        # Detections speichern
        BENCHMARKING_SERVICE.set_detections(detections)

        # Zurück zu Idle (simuliert Ende der Analyse, zurück zum Hören)
        time.sleep(2)  # Kurze Idle-Periode nach Analyse

        # Assertions: Prüfe, ob die Pipeline erfolgreich war
        self.assertGreater(len(detections), 0, "No detections found – pipeline failed")
        expected_sci_names = ['Pica pica']  # Basierend auf Test-Datei
        for det in detections:
            self.assertIn(det.scientific_name, expected_sci_names, "Unexpected species detected")

        # Zusätzliche Checks: Timer-Stats validieren vor dem Reset durch log_results_to_csv()
        analysis_stats = BENCHMARKING_SERVICE.get_timer_stats(BenchmarkTimerNames.TOTAL_ANALYSIS.value)
        self.assertGreater(analysis_stats['total_wall_s'], 0, "Analysis took no time")
        reporting_stats = BENCHMARKING_SERVICE.get_timer_stats(BenchmarkTimerNames.TOTAL_REPORTING.value)
        self.assertGreater(reporting_stats['total_wall_s'], 0, "Reporting took no time")

        # Ergebnisse loggen und ausgeben
        BENCHMARKING_SERVICE.print_summary()
        BENCHMARKING_SERVICE.log_results_to_csv()

        # Mock-Verifizierungen: Stelle sicher, dass DB und Notifications simuliert wurden
        mock_write_to_db.assert_called()  # DB-Schreibfunktion wurde aufgerufen
        mock_apprise.assert_called()  # Apprise notifications wurden simuliert

if __name__ == '__main__':
    unittest.main()