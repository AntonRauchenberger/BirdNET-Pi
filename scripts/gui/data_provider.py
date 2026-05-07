"""
Provides state data for the GUI screens.
"""

import datetime
import socket
import sqlite3
import threading

from pathlib import Path
from typing import Any


class DataProvider:

    def __init__(self, db_path: str):
        self._db_con = sqlite3.connect(db_path, check_same_thread=False)
        self._db_lock = threading.Lock()

    def _get_from_db(self, query: str, params: tuple = ()) -> list:
        for attempt_number in range(3):
            try:
                with self._db_lock:
                    cur = self._db_con.cursor()
                    cur.execute(query, params)
                    return cur.fetchall()
            except BaseException as e:
                pass

    @staticmethod
    def _get_boot_time() -> datetime.datetime:
        uptime_seconds = float(Path("/proc/uptime").read_text().split()[0])
        return datetime.datetime.now() - datetime.timedelta(seconds=uptime_seconds)

    def fetch_initial_state_data(self) -> dict:
        last_detection = self._get_from_db("SELECT com_name, confidence, count(*) as total_detections FROM detections ORDER BY date DESC, time DESC LIMIT 1")

        boot_time = self._get_boot_time()
        uptime_days = (datetime.datetime.now() - boot_time).days

        confidence_value = "N/A"
        if last_detection and last_detection[0][1] is not None:
            confidence_value = int(last_detection[0][1] * 100)

        return {
            "last_detected_bird": last_detection[0][0] if last_detection else "N/A",
            "last_detected_confidence": confidence_value,
            "total_detections": last_detection[0][2] if last_detection else "N/A",
            "active since_date": boot_time.strftime("%Y-%m-%d"),
            "active since_days": str(uptime_days),
            "system_name": socket.gethostname(),
        }

    def fetch_list_state_data(self, current_page: int = 1) -> dict:
        bird_list = self._get_from_db("SELECT com_name, COUNT(*) AS amount FROM detections GROUP BY Com_Name ORDER BY amount DESC")

        if bird_list is None:
            formated_bird_list = [{"common_name": "Nothing found yet", "amount": 0}]
        else:
            formated_bird_list = [{"common_name": row[0], "amount": row[1]} for row in bird_list]

        return {
            "current_page": current_page,
            "bird_list": formated_bird_list,
        }

    def fetch_sync_state_data(self) -> dict:
        # In a real implementation, this would fetch the current sync status from the backend.
        return {
            "wlan_ssid": "MyWiFiNetwork_1",
            "status": "Ready",
            "last_sync": "2024-06-01 12:34:56",
            "entries_to_sync": 42,
        }

    def fetch_gps_state_data(self) -> dict:
        # In a real implementation, this would fetch the current GPS status and coordinates from the backend.
        return {
            "status": "ON",
            "latitude": "52.5200 N",
            "longitude": "13.4050 E",
            "last_update": "2024-06-01 12:34:56",
        }

    def get_list_total_pages(self, page_size: int) -> int:
        return max(1, (len(self.fetch_list_state_data()["bird_list"]) + page_size - 1) // page_size)
    
    def get_latest_bird_detections(self, limit=20) -> list[dict]:
        latest_detections = self._get_from_db("SELECT * FROM detections ORDER BY date DESC, time DESC LIMIT ?", (limit,))

        if latest_detections is None:
            return []
        
        return latest_detections
    
    def get_sync_data(self) -> list[Any]:
        # TODO get real sync data
        return [
            {
                "date": "2024-06-01",
                "time": "12:34:56",
                "sci_name": "Turdus merula",
                "com_name": "Common Blackbird",
                "confidence": 0.95,
                "lat": "52.5200",
                "lon": "13.4050",
                "cutoff": 0.7,
                "week": 19,
                "sens": 1.25,
                "overlap": 0,
            },
            {
                "date": "2024-06-01",
                "time": "12:34:56",
                "sci_name": "Turdus merula",
                "com_name": "Common Blackbird",
                "confidence": 0.95,
                "lat": "52.5200",
                "lon": "13.4050",
                "cutoff": 0.7,
                "week": 19,
                "sens": 1.25,
                "overlap": 0,
            },
            {
                "date": "2024-06-01",
                "time": "12:34:56",
                "sci_name": "Turdus merula",
                "com_name": "Common Blackbird",
                "confidence": 0.95,
                "lat": "52.5200",
                "lon": "13.4050",
                "cutoff": 0.7,
                "week": 19,
                "sens": 1.25,
                "overlap": 0,
            }
        ]
