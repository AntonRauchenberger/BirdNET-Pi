"""GPS background service loop for periodic location updates."""

import time

try:
    from .receiver import GPSReceiver
except ImportError:
    from gps.receiver import GPSReceiver

try:
    from ..utils.helpers import get_settings
except ImportError:
    from utils.helpers import get_settings


SETTINGS_POLL_INTERVAL_SECONDS = 2
DEFAULT_GPS_INTERVAL_SECONDS = 1800


class GPSService:
    def __init__(self, poll_interval_seconds: int = SETTINGS_POLL_INTERVAL_SECONDS):
        self.poll_interval_seconds = max(1, int(poll_interval_seconds))
        self.running = True
        self._last_enabled = False
        self._next_update_at = 0.0

    @staticmethod
    def _is_enabled(settings) -> bool:
        return str(settings.get("GPS_UPDATES_ENABLED", "0")).strip().lower() in {"1", "true", "yes", "on"}
    
    def _power_save_mode_enabled(self, settings) -> bool:
        return str(settings.get("GPS_POWER_SAVE_MODE", "1")).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _get_interval_seconds(settings) -> int:
        try:
            interval_seconds = int(settings.get("GPS_INTERVAL", DEFAULT_GPS_INTERVAL_SECONDS))
        except (TypeError, ValueError):
            interval_seconds = DEFAULT_GPS_INTERVAL_SECONDS

        return max(1, interval_seconds)

    def stop(self) -> None:
        self.running = False

    def run(self) -> None:
        pre_settings = get_settings(force_reload=True)
        pre_gps_enabled = self._is_enabled(pre_settings)
        pre_gps_power_save_mode_enabled = self._power_save_mode_enabled(pre_settings)
        GPSReceiver.activate_sleep_mode(pre_gps_power_save_mode_enabled, force=not pre_gps_enabled)

        while self.running:
            try:
                settings = get_settings(force_reload=True)
                gps_power_save_mode_enabled = self._power_save_mode_enabled(settings)
                gps_enabled = self._is_enabled(settings)
                gps_interval_seconds = self._get_interval_seconds(settings)

                if not gps_enabled:
                    if self._last_enabled:
                        GPSReceiver.activate_sleep_mode(gps_power_save_mode_enabled, force=True)
                    self._last_enabled = False
                    self._next_update_at = 0.0
                    time.sleep(self.poll_interval_seconds)
                    continue

                now = time.monotonic()
                if not self._last_enabled:
                    self._next_update_at = 0.0

                self._last_enabled = True

                if now >= self._next_update_at:
                    GPSReceiver.handle_gps_work(True, gps_power_save_mode_enabled)
                    self._next_update_at = time.monotonic() + gps_interval_seconds
                    continue

                sleep_seconds = min(self.poll_interval_seconds, max(0.0, self._next_update_at - now))
                time.sleep(sleep_seconds)
            except Exception as exc:
                print(f"GPS service loop error: {exc}")
                time.sleep(self.poll_interval_seconds)

        GPSReceiver.activate_sleep_mode(gps_power_save_mode_enabled, force=True)
