"""
Sync power test with DB setup, hotspot and sync runtime phases, and safe restoration.

Process:
1. 5 minutes rest
2. Enable hotspot via GUI, verify state change
3. 30 minutes hotspot active with sync simulation after 15 minutes
4. Disable hotspot via GUI, verify state change
5. 5 minutes rest
"""

import datetime
import sqlite3
import subprocess
import sys
import time

from pathlib import Path

# Setup logging to file
LOG_FILE = Path("/tmp/test_sync_power.log")


class Logger:
	"""Log to both console and file."""
	def __init__(self, filepath: Path):
		self.filepath = filepath
		self.file = open(filepath, "w")
	
	def write(self, msg: str):
		sys.__stdout__.write(msg)
		self.file.write(msg)
		self.file.flush()
	
	def flush(self):
		self.file.flush()
	
	def close(self):
		self.file.close()

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(REPO_ROOT))

# Test configuration
BACKEND = "waveshare"
LIST_PAGE = 1
CLEAR_DISPLAY_ON_START = True
DB_PATH = REPO_ROOT / "scripts" / "birds.db"
ROWS = 1000
REST_SECONDS = 300
HOTSPOT_SECONDS = 1800
SYNC_AFTER_SECONDS = 900
SYNC_BATCH_SIZE = 50
DISPLAY_SERVICE = "birdnet_display_gui.service"

from scripts.gui.manager import GUIManager, StateNames

def create_detections_table(db_path: Path) -> None:
	con = sqlite3.connect(db_path)
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
			  File_Name VARCHAR(100) NOT NULL,
			  Synced BOOLEAN DEFAULT FALSE,
			  Uncommon BOOLEAN DEFAULT FALSE
			)
			"""
		)
		con.commit()
	finally:
		con.close()


def seed_detections(db_path: Path, rows: int) -> None:
	con = sqlite3.connect(db_path)
	try:
		cur = con.cursor()
		base_timestamp = datetime.datetime(2026, 1, 1, 0, 0, 0)

		for i in range(1, rows + 1):
			timestamp = base_timestamp + datetime.timedelta(seconds=i * 17)
			cur.execute(
				"""
				INSERT INTO detections (
					Date, Time, Sci_Name, Com_Name, Confidence, Lat, Lon,
					Cutoff, Week, Sens, Overlap, File_Name, Synced, Uncommon
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				(
					timestamp.strftime("%Y-%m-%d"),
					timestamp.strftime("%H:%M:%S"),
					"Parus major",
					"Great Tit",
					0.91,
					49.02,
					12.09,
					0.7,
					int(timestamp.strftime("%W")),
					1.25,
					0.0,
					f"sync_power_test_{i:04d}.wav",
					0,
					0,
				),
			)

		con.commit()
	finally:
		con.close()


def verify_detection_count(db_path: Path, expected_rows: int) -> None:
	con = sqlite3.connect(db_path)
	try:
		cur = con.cursor()
		cur.execute("SELECT COUNT(*) FROM detections")
		count = cur.fetchone()[0]
	finally:
		con.close()

	if count != expected_rows:
		raise RuntimeError(f"Expected {expected_rows} detections, found {count}")


def wait_phase(seconds: int, phase_name: str) -> None:
	print(f"{phase_name} for {seconds} seconds...")
	start = time.monotonic()
	next_log = 60

	while True:
		elapsed = int(time.monotonic() - start)
		if elapsed >= seconds:
			break

		if elapsed >= next_log:
			remaining = max(0, seconds - elapsed)
			print(f"{phase_name}: {remaining} seconds remaining")
			next_log += 60

		time.sleep(1)


def simulate_sync_of_pending_detections(manager: GUIManager, limit: int = 50) -> int:
	"""Simulate app sync by fetching pending rows in batches until none are left."""
	total_synced = 0
	while True:
		batch = manager.data_provider.get_sync_data(offset=0, limit=limit)
		if not batch:
			break
		total_synced += len(batch)
		print(f"Sync simulation: fetched {len(batch)} rows (total {total_synced})")

	print(f"Sync simulation completed: {total_synced} rows synced")
	return total_synced


def run_hotspot_phase_with_sync(
	manager: GUIManager,
	hotspot_seconds: int,
	sync_after_seconds: int,
	sync_batch_size: int,
) -> int:
	print(f"Hotspot active phase for {hotspot_seconds} seconds...")
	start = time.monotonic()
	next_log = 60
	sync_done = False
	synced_rows = 0

	while True:
		elapsed = int(time.monotonic() - start)
		if elapsed >= hotspot_seconds:
			break

		if not sync_done and elapsed >= sync_after_seconds:
			print(f"Starting sync simulation after {elapsed} seconds of hotspot runtime")
			synced_rows = simulate_sync_of_pending_detections(manager, limit=sync_batch_size)
			sync_done = True
			manager.render_current_state()

		if elapsed >= next_log:
			remaining = max(0, hotspot_seconds - elapsed)
			print(f"Hotspot active phase: {remaining} seconds remaining")
			next_log += 60

		time.sleep(1)

	if not sync_done:
		print("Hotspot phase ended before sync trigger time; running sync simulation now")
		synced_rows = simulate_sync_of_pending_detections(manager, limit=sync_batch_size)
		manager.render_current_state()

	return synced_rows


def shutdown_manager(manager: GUIManager | None) -> None:
	if manager is None:
		return

	try:
		if manager.screen_reset_timer is not None:
			manager.screen_reset_timer.cancel()
	except Exception:
		pass

	try:
		db_con = getattr(manager.data_provider, "_db_con", None)
		if db_con is not None:
			db_con.close()
	except Exception:
		pass

	try:
		if hasattr(manager.device, "sleep"):
			manager.device.sleep()
	except Exception:
		pass


def backup_database(db_path: Path) -> tuple[Path, bool]:
	backup_path = db_path.with_name(f"{db_path.name}.sync_test_backup")
	if backup_path.exists():
		raise RuntimeError(f"Backup already exists: {backup_path}")

	had_original = db_path.exists()
	if had_original:
		db_path.rename(backup_path)

	return backup_path, had_original


def restore_database(db_path: Path, backup_path: Path, had_original: bool) -> None:
	if db_path.exists():
		db_path.unlink()

	if had_original and backup_path.exists():
		backup_path.rename(db_path)


def stop_display_service(service_name: str) -> bool:
	status = subprocess.run(
		["systemctl", "is-active", service_name],
		check=False,
		capture_output=True,
		text=True,
	)

	if status.returncode != 0 or status.stdout.strip() != "active":
		print(f"Service {service_name} is not active, continuing without stop")
		return False

	print(f"Stopping service {service_name}...")
	stop_result = subprocess.run(
		["sudo", "systemctl", "stop", service_name],
		check=False,
		capture_output=True,
		text=True,
	)

	if stop_result.returncode != 0:
		raise RuntimeError(
			f"Failed to stop {service_name}: {stop_result.stderr.strip() or stop_result.stdout.strip()}"
		)

	print(f"Service {service_name} stopped")
	return True


def start_display_service(service_name: str, should_restart: bool) -> None:
	if not should_restart:
		return

	print(f"Starting service {service_name}...")
	start_result = subprocess.run(
		["sudo", "systemctl", "start", service_name],
		check=False,
		capture_output=True,
		text=True,
	)

	if start_result.returncode != 0:
		raise RuntimeError(
			f"Failed to start {service_name}: {start_result.stderr.strip() or start_result.stdout.strip()}"
		)

	print(f"Service {service_name} started")


def go_to_state(manager: GUIManager, target_state: StateNames) -> None:
	max_steps = len(manager.states) + 2
	for _ in range(max_steps):
		if manager.current_state.name == target_state:
			return
		manager.handle_next()

	raise RuntimeError(f"Failed to navigate to state {target_state.value}")


def wait_for_hotspot_state(manager: GUIManager, enabled: bool, timeout_seconds: int = 15) -> None:
	deadline = time.monotonic() + timeout_seconds
	while time.monotonic() < deadline:
		if manager.data_provider.is_hotspot_enabled() == enabled:
			return
		time.sleep(0.5)

	state_text = "enabled" if enabled else "disabled"
	raise RuntimeError(f"Hotspot did not become {state_text} in time")


def toggle_hotspot_via_ok(manager: GUIManager, enabled: bool) -> None:
	go_to_state(manager, StateNames.SYNC)
	current = manager.data_provider.is_hotspot_enabled()

	if current == enabled:
		print(f"Hotspot already {'enabled' if enabled else 'disabled'}")
		manager.render_current_state()
		return

	print(f"Toggling hotspot to {'enabled' if enabled else 'disabled'} via OK action on SYNC screen")
	manager.handle_ok()
	wait_for_hotspot_state(manager, enabled)
	manager.render_current_state()


def main() -> int:
	logger = Logger(LOG_FILE)
	original_stdout = sys.stdout
	sys.stdout = logger

	db_path = DB_PATH.expanduser().resolve()

	backup_path = db_path.with_name(f"{db_path.name}.sync_test_backup")
	had_original = False
	manager = None
	should_restart_service = False

	try:
		print(f"Starting sync power test, logging to {LOG_FILE}")
		print(f"Backing up current database: {db_path}")
		backup_path, had_original = backup_database(db_path)

		print("Creating test database...")
		create_detections_table(db_path)
		seed_detections(db_path, ROWS)
		verify_detection_count(db_path, ROWS)
		print(f"Inserted {ROWS} detections")

		if BACKEND == "waveshare":
			should_restart_service = stop_display_service(DISPLAY_SERVICE)

		manager = GUIManager(
			start_state=StateNames.START,
			list_page=LIST_PAGE,
			backend=BACKEND,
			clear=CLEAR_DISPLAY_ON_START,
		)

		wait_phase(REST_SECONDS, "Rest phase #1")
		toggle_hotspot_via_ok(manager, enabled=True)
		synced_rows = run_hotspot_phase_with_sync(
			manager,
			hotspot_seconds=HOTSPOT_SECONDS,
			sync_after_seconds=SYNC_AFTER_SECONDS,
			sync_batch_size=SYNC_BATCH_SIZE,
		)
		toggle_hotspot_via_ok(manager, enabled=False)
		wait_phase(REST_SECONDS, "Rest phase #2")

		print(f"Sync hotspot power test finished successfully (synced rows: {synced_rows})")
		return 0

	except KeyboardInterrupt:
		print("Interrupted by signal. Starting cleanup...")
		return 130
	except Exception as exc:
		print(f"Sync hotspot power test failed: {exc}")
		return 1
	finally:
		if manager is not None:
			try:
				toggle_hotspot_via_ok(manager, enabled=False)
			except Exception:
				pass

		shutdown_manager(manager)
		try:
			restore_database(db_path, backup_path, had_original)
			print("Original database restored")
		except Exception as exc:
			print(f"Failed to restore original database: {exc}")

		try:
			start_display_service(DISPLAY_SERVICE, should_restart_service)
		except Exception as exc:
			print(f"Failed to restart display service: {exc}")

		sys.stdout = original_stdout
		logger.close()
		print(f"Test logs saved to {LOG_FILE}")


if __name__ == "__main__":
	main()
