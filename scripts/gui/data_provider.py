"""
Provides state data for the GUI screens.
"""

import datetime
import socket
import sqlite3
import subprocess
import shutil
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

    def _execute_db_command(self, command: str, params: tuple = ()) -> None:
        for attempt_number in range(3):
            try:
                with self._db_lock:
                    cur = self._db_con.cursor()
                    cur.execute(command, params)
                    self._db_con.commit()
                    return
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
        entries_to_sync = self.get_sync_pending_detections_amount()
        hotspot_enabled = self.is_hotspot_enabled()

        if hotspot_enabled:
            wifi_ssid = self._get_hotspot_ssid()
            hotspot_ip = self._get_wifi_ip()
            hotspot_ip = hotspot_ip if hotspot_ip != "Not connected" else "192.168.4.1"
            status = "Sync Aktiv"
            app_url = f"http://{hotspot_ip}/app"
        else:
            wifi_ssid = self._get_wifi_ssid()
            if wifi_ssid != "Not connected" and self._has_internet_connectivity():
                status = "Online"
                app_url = "http://birdnetpi.local/app"
            else:
                status = "Offline"
                app_url = "Not connected"

        return {
            "wlan_ssid": wifi_ssid,
            "status": status,
            "entries_to_sync": entries_to_sync,
            "app_url": app_url,
        }

    def toggle_hotspot(self) -> bool:
        """Toggle hotspot state via the shell scripts and return resulting state."""
        scripts_dir = Path(__file__).resolve().parent.parent
        enable_script = scripts_dir / "activate_hotspot.sh"
        disable_script = scripts_dir / "deactivate_hotspot.sh"

        try:
            target_script = disable_script if self.is_hotspot_enabled() else enable_script
            if not target_script.exists():
                print(f"Hotspot script not found: {target_script}")
                return self.is_hotspot_enabled()

            result = subprocess.run(["bash", str(target_script)], check=False, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Hotspot toggle failed ({result.returncode}): {result.stderr.strip()}")
        except Exception as e:
            print(f"Error toggling hotspot: {e}")

        return self.is_hotspot_enabled()

    def is_hotspot_enabled(self) -> bool:
        """Check whether the configured hotspot connection is currently active."""
        connection_name = self._get_hotspot_connection_name()
        if connection_name == "Not connected":
            return False

        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"],
                check=False,
                capture_output=True,
                text=True,
            )
            active_names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return connection_name in active_names
        except Exception as e:
            print(f"Error checking hotspot status: {e}")
            return False

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
    
    def get_sync_pending_detections_amount(self) -> int:
        pending_detections = self._get_from_db("SELECT COUNT(*) FROM detections WHERE synced = FALSE")

        if pending_detections is None:
            return 0
        
        return pending_detections[0][0]
    
    def get_sync_data(self, offset: int = 0, limit: int = 50) -> list[Any]:
        detections = self._get_from_db("SELECT * FROM detections WHERE synced = FALSE LIMIT ? OFFSET ?", (limit, offset))

        if detections is None:
            return []

        formated_detections = []
        fetchedTimestamps = []
        for row in detections:
            formated_detections.append({
                "date": row[0],
                "time": row[1],
                "sci_name": row[2],
                "com_name": row[3],
                "confidence": row[4],
                "lat": row[5],
                "lon": row[6],
                "cutoff": row[7],
                "weekday": row[8],
                "sens": row[9],
                "overlap": row[10],
                "file_name": row[11],
            })
            fetchedTimestamps.append((row[0], row[1]))

        # Mark these detections as synced in the database using the date and time as identifiers
        if formated_detections:
            placeholders = ",".join(["(?, ?)"] * len(fetchedTimestamps))
            params = [item for timestamp in fetchedTimestamps for item in timestamp]
            self._execute_db_command(f"UPDATE detections SET synced = TRUE WHERE (date, time) IN ({placeholders})", tuple(params))
            
        
        return formated_detections
    
    def delete_synced_data(self) -> None:
        self._execute_db_command("DELETE FROM detections WHERE synced = TRUE")

    
    def _get_battery_percentage(self) -> int:
        # TODO implement
        return 100

    def _get_device_location(self) -> dict | None:
        # TODO implement
        return {"latitude": 49.0200, "longitude": 12.0900}
    
    def _get_storage_usage_percent(self) -> int:
        """Get storage usage percentage of root filesystem"""
        try:
            usage = shutil.disk_usage("/")
            percent = int((usage.used / usage.total) * 100)
            return percent
        except Exception:
            return 0
    
    def _get_wifi_ssid(self) -> str:
        """Get currently connected Wi-Fi SSID from NetworkManager."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
                check=False,
                capture_output=True,
                text=True,
            )

            for line in result.stdout.splitlines():
                if line.startswith("yes:"):
                    ssid = line.split(":", 1)[1].strip()
                    if ssid:
                        return ssid
        except Exception as e:
            print(f"Error reading SSID: {e}")
        
        return "Not connected"

    def _get_hotspot_ssid(self) -> str:
        """Get the hotspot SSID from activate_hotspot.sh."""
        try:
            hotspot_script = Path(__file__).resolve().parent.parent / "activate_hotspot.sh"

            if not hotspot_script.exists():
                return "Hotspot"

            content = hotspot_script.read_text()

            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("SSID="):
                    ssid_part = line[5:]
                    ssid = ssid_part.strip().strip('"')
                    if ssid:
                        return ssid
        except Exception as e:
            print(f"Error reading hotspot SSID: {e}")

        return "Hotspot"

    def _get_wifi_ip(self) -> str:
        """Get the hotspot IP from activate_hotspot.sh"""
        try:
            # Navigate to scripts folder (parent of gui folder)
            hotspot_script = Path(__file__).resolve().parent.parent / "activate_hotspot.sh"
            
            if not hotspot_script.exists():
                return "Not connected"
            
            content = hotspot_script.read_text()
            
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("IP_ADDR="):
                    # Extract IP from line like: IP_ADDR="192.168.4.1/24" and remove mask.
                    ip_part = line[8:]
                    ip = ip_part.strip().strip('"')
                    if ip:
                        return ip.split("/")[0]
        except Exception as e:
            print(f"Error reading IP: {e}")
        
        return "Not connected"

    def _get_device_ip(self) -> str:
        """Get current device IP address used for outbound traffic."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                # This does not send traffic; it asks the OS for the default route source IP.
                sock.connect(("8.8.8.8", 80))
                ip = sock.getsockname()[0]
                if ip and ip != "127.0.0.1":
                    return ip
        except Exception:
            pass

        try:
            # Fallback for environments without a default route at the moment.
            for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
                if ip and not ip.startswith("127."):
                    return ip
        except Exception:
            pass

        return "Not connected"

    def _get_hotspot_connection_name(self) -> str:
        """Get hotspot connection name from activate_hotspot.sh."""
        try:
            hotspot_script = Path(__file__).resolve().parent.parent / "activate_hotspot.sh"
            if not hotspot_script.exists():
                return "Not connected"

            content = hotspot_script.read_text()
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("CON_NAME="):
                    name_part = line[9:]
                    name = name_part.strip().strip('"')
                    if name:
                        return name
        except Exception as e:
            print(f"Error reading hotspot connection name: {e}")

        return "Not connected"

    def _has_internet_connectivity(self) -> bool:
        """Return True if NetworkManager reports internet connectivity."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "CONNECTIVITY", "general"],
                check=False,
                capture_output=True,
                text=True,
            )
            connectivity = result.stdout.strip().lower()
            return connectivity == "full"
        except Exception:
            return False
    
    def get_device_details(self) -> dict:
        device_name = socket.gethostname()
        
        battery_percentage = self._get_battery_percentage()
        
        storage_usage_percent = self._get_storage_usage_percent()
        
        boot_time = self._get_boot_time()
        uptime_days = (datetime.datetime.now() - boot_time).days
        
        wifi_ssid = self._get_wifi_ssid()
        location = self._get_device_location()
        
        return {
            "name": device_name,
            "battery": battery_percentage,
            "storage": storage_usage_percent,
            "uptime": uptime_days,
            "ssid": wifi_ssid,
            "longitude": location["longitude"] if location else None,
            "latitude": location["latitude"] if location else None,
            "lastUpdate": datetime.datetime.now(),
        }
