#!/usr/bin/env python3

"""Display GUI power test with deterministic DB setup and safe restoration."""

import argparse
import datetime
import sqlite3
import subprocess
import sys
import time

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(REPO_ROOT))

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
					f"display_power_test_{i:04d}.wav",
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


def run_stress_cycle(manager: GUIManager, stress_seconds: int, switch_interval: int) -> int:
	print(
		"Starting stress phase: "
		f"switch state every {switch_interval} seconds for {stress_seconds} seconds"
	)

	started = time.monotonic()
	switches = 0

	while True:
		elapsed = int(time.monotonic() - started)
		if elapsed >= stress_seconds:
			break

		manager.handle_next()
		switches += 1
		current = manager.current_state.name.value
		print(f"Switch {switches}: current state={current}")

		for _ in range(switch_interval):
			if int(time.monotonic() - started) >= stress_seconds:
				break
			time.sleep(1)

	return switches


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
	backup_path = db_path.with_name(f"{db_path.name}.display_test_backup")
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
	"""Stop display service if it is active. Returns True if we should start it again later."""
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


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Display GUI stress test with DB backup/restore")
	parser.add_argument("--backend", choices=["auto", "emulator", "waveshare"], default="waveshare")
	parser.add_argument("--list-page", type=int, default=1)
	parser.add_argument("--no-clear", action="store_true", help="Do not clear display on startup")
	parser.add_argument("--db-path", default=str(REPO_ROOT / "scripts" / "birds.db"))
	parser.add_argument("--rows", type=int, default=1000)
	parser.add_argument("--rest-seconds", type=int, default=300)
	parser.add_argument("--stress-seconds", type=int, default=300)
	parser.add_argument("--switch-interval", type=int, default=15)
	parser.add_argument("--display-service", default="birdnet_display_gui.service")
	return parser.parse_args()


def main() -> int:
	args = parse_args()

	db_path = Path(args.db_path).expanduser().resolve()

	backup_path = db_path.with_name(f"{db_path.name}.display_test_backup")
	had_original = False
	manager = None
	should_restart_service = False

	try:
		if args.backend == "waveshare":
			should_restart_service = stop_display_service(args.display_service)

		print(f"Backing up current database: {db_path}")
		backup_path, had_original = backup_database(db_path)

		print("Creating deterministic test database...")
		create_detections_table(db_path)
		seed_detections(db_path, args.rows)
		verify_detection_count(db_path, args.rows)
		print(f"Inserted {args.rows} detections")

		manager = GUIManager(
			start_state=StateNames.START,
			list_page=args.list_page,
			backend=args.backend,
			clear=not args.no_clear,
		)

		wait_phase(args.rest_seconds, "Rest phase #1")
		switches = run_stress_cycle(manager, args.stress_seconds, args.switch_interval)
		wait_phase(args.rest_seconds, "Rest phase #2")
		print(f"Display stress test finished successfully with {switches} screen switches")
		return 0

	except KeyboardInterrupt:
		print("Interrupted by signal. Starting cleanup...")
		return 130
	except Exception as exc:
		print(f"Display stress test failed: {exc}")
		return 1
	finally:
		shutdown_manager(manager)
		try:
			restore_database(db_path, backup_path, had_original)
			print("Original database restored")
		except Exception as exc:
			print(f"Failed to restore original database: {exc}")

		try:
			start_display_service(args.display_service, should_restart_service)
		except Exception as exc:
			print(f"Failed to restart display service: {exc}")


if __name__ == "__main__":
	raise SystemExit(main())
