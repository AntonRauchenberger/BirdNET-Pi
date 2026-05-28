"""
Provides state data for the GUI screens.
"""

import datetime
import socket
import sqlite3
import subprocess
import shutil
import threading
import time

from pathlib import Path
from typing import Any

from fastapi.responses import FileResponse

try:
    from ..utils.helpers import get_settings, save_settings
except ImportError:
    from utils.helpers import get_settings, save_settings


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
        (entries_to_sync, _) = self.get_sync_pending_detections_amount()
        hotspot_enabled = self.is_hotspot_enabled()

        if hotspot_enabled:
            wifi_ssid = self._get_hotspot_ssid()
            hotspot_ip = self._get_wifi_ip()
            hotspot_ip = hotspot_ip if hotspot_ip != "Not connected" else "192.168.4.1"
            status = "Active"
            app_url = "tinyurl.com/amuecpf2"
        else:
            wifi_ssid = self._get_wifi_ssid()
            if wifi_ssid != "Not connected" and self._has_internet_connectivity():
                status = "Online"
                app_url = "tinyurl.com/amuecpf2"
            else:
                status = "Offline"
                app_url = "tinyurl.com/amuecpf2"

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
            hotspot_enabled_before = self.is_hotspot_enabled()
            target_script = disable_script if hotspot_enabled_before else enable_script
            if not target_script.exists():
                print(f"Hotspot script not found: {target_script}")
                return self.is_hotspot_enabled()

            result = subprocess.run(["bash", str(target_script)], check=False, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Hotspot toggle failed ({result.returncode}): {result.stderr.strip()}")
                return self.is_hotspot_enabled()

            desired_hotspot_state = not hotspot_enabled_before
            return self._wait_for_hotspot_state(desired_hotspot_state)
        except Exception as e:
            print(f"Error toggling hotspot: {e}")

        return self.is_hotspot_enabled()

    def is_hotspot_enabled(self) -> bool:
        """Check whether the configured hotspot connection is currently active."""
        connection_name = self._get_hotspot_connection_name()
        if connection_name == "Not connected":
            return False

        try:
            active_wifi_connection = self._get_active_wifi_connection_name()
            if active_wifi_connection:
                return active_wifi_connection == connection_name

            result = subprocess.run(
                ["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "dev", "status"],
                check=False,
                capture_output=True,
                text=True,
            )
            for line in result.stdout.splitlines():
                device, state, active_connection = (line.split(":", 2) + ["", "", ""])[:3]
                if device.startswith("wlan") and state.startswith("connected") and active_connection == connection_name:
                    return True

            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"],
                check=False,
                capture_output=True,
                text=True,
            )
            active_names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return connection_name in active_names
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error checking hotspot status: {e}")
            return False

    def _wait_for_hotspot_state(self, expected_enabled: bool, timeout_seconds: float = 10.0) -> bool:
        """Wait briefly until NetworkManager reflects the expected hotspot state."""
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self.is_hotspot_enabled() == expected_enabled:
                return expected_enabled
            time.sleep(0.4)
        return self.is_hotspot_enabled()

    def _get_active_wifi_connection_name(self) -> str | None:
        """Return active Wi-Fi connection name from NetworkManager device status."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"],
                check=False,
                capture_output=True,
                text=True,
                timeout=1.5,
            )

            for line in result.stdout.splitlines():
                parts = line.split(":", 3)
                if len(parts) < 4:
                    continue
                device, dev_type, state, connection = parts
                if not device.startswith("wlan"):
                    continue
                if dev_type != "wifi":
                    continue
                if state != "connected":
                    continue
                connection = connection.strip()
                if connection and connection != "--":
                    return connection
        except Exception:
            return None

        return None

    def fetch_gps_state_data(self) -> dict:
        deviceSettings = get_settings()
        currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "latitude": deviceSettings.get("latitude", "0.0"),
            "longitude": deviceSettings.get("longitude", "0.0"),
            "last_update": deviceSettings.get("last_gps_update", currentTime),
        }

    def get_list_total_pages(self, page_size: int) -> int:
        return max(1, (len(self.fetch_list_state_data()["bird_list"]) + page_size - 1) // page_size)
    
    def get_latest_bird_detections(self, limit=20) -> list[dict]:
        latest_detections = self._get_from_db("SELECT * FROM detections ORDER BY date DESC, time DESC LIMIT ?", (limit,))

        if latest_detections is None:
            return []
        
        return latest_detections
    
    def get_sync_pending_detections_amount(self) -> tuple[int, int]:
        pending_detections = self._get_from_db("SELECT COUNT(*) FROM detections WHERE synced = FALSE")

        if pending_detections is None:
            return 0, 0
        
        pending_species = self._get_from_db("SELECT DISTINCT com_name FROM detections WHERE synced = FALSE")
        
        return pending_detections[0][0], len(pending_species) if pending_species else 0
    
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
    
    def delete_synced_data(self, AUDIO_PATH: str) -> None:
        # Delete corresponding audio files for synced detections
        synced_detections = self._get_from_db("SELECT date, com_name, file_name FROM detections WHERE synced = TRUE")
        for detection in synced_detections:
            date = detection[0]
            com_name = detection[1]
            file_name = detection[2]
            com_name_formatted = com_name.replace(" ", "_").replace("'", "")
            file_path = Path(AUDIO_PATH) / date / com_name_formatted / file_name
            try:
                if file_path.exists():
                    file_path.unlink()
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Error deleting audio file {file_path}: {e}")

        self._execute_db_command("DELETE FROM detections WHERE synced = TRUE")

    
    def _get_battery_percentage(self) -> int:
        # TODO implement
        return 100

    def _get_device_location(self) -> dict | None:
        deviceSettings = get_settings()
    
        latitude = deviceSettings.get("latitude", 49.0200)
        longitude = deviceSettings.get("longitude", 12.0900)

        return {"latitude": latitude, "longitude": longitude}
    
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
        hotspot_connection_name = self._get_hotspot_connection_name()

        active_wifi_connection = self._get_active_wifi_connection_name()
        if active_wifi_connection and active_wifi_connection != hotspot_connection_name:
            return active_wifi_connection

        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
                check=False,
                capture_output=True,
                text=True,
                timeout=1.0 
            )

            for line in result.stdout.splitlines():
                if line.startswith("yes:"):
                    ssid = line.split(":", 1)[1].strip()
                    if ssid and ssid != self._get_hotspot_ssid():
                        return ssid
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
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
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(0.1)
                sock.connect(("8.8.8.8", 80))
                ip = sock.getsockname()[0]
                if ip and ip != "127.0.0.1":
                    return ip
        except Exception:
            pass

        try:
            for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
                if ip and not ip.startswith("127."):
                    return ip
        except Exception:
            pass

        return "192.168.4.1" # IP from hotspot

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

    def get_audio_file(self, audio_path: str, species_com_name: str) -> FileResponse | None:
        best_detection = self._get_from_db(
            """
            SELECT Date, Time, File_Name, Com_Name, Confidence
            FROM detections
            WHERE Com_Name = ?
            ORDER BY Date DESC, Time DESC, Confidence DESC
            LIMIT 1
            """,
            (species_com_name,),
        )

        if not best_detection:
            return None

        detection = best_detection[0]
        detection_date = detection[0]
        detection_com_name = detection[3].replace(" ", "_").replace("'", "")
        detection_file_name = detection[2]

        file_path = Path(audio_path) / detection_date / detection_com_name / detection_file_name

        if file_path.exists():
            return FileResponse(str(file_path), media_type="audio/wav")

        return None
    
    def get_device_settings(self) -> dict | None:
        conf = get_settings()
        return conf

    def update_device_settings(self, new_settings: dict) -> None:
        save_settings(new_settings=new_settings)
