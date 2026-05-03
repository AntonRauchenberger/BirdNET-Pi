"""
Controls which screen is active and handles the transition between them.
"""

import argparse
import os
import sys
import time
import threading

from pathlib import Path

from enum import Enum

# Allow direct execution via "python3 manager.py"
if __package__ is None or __package__ == "":
    gui_dir = Path(__file__).resolve().parent
    if str(gui_dir) not in sys.path:
        sys.path.insert(0, str(gui_dir))

    from input_handler import ButtonInputHandler
    from renderer import render
    from display_driver import create_device
    from data_provider import DataProvider
else:
    from .input_handler import ButtonInputHandler
    from .renderer import render
    from .display_driver import create_device
    from .data_provider import DataProvider

# Derive DB_PATH locally to avoid a circular import with scripts.utils.helpers
_REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = str(_REPO_ROOT / "scripts" / "birds.db")

class StateNames(Enum):
    START = "START"
    ANALYZE_RESULT = "ANALYZE_RESULT"
    LIVE_ANALYZE = "LIVE_ANALYZE"
    LIST = "LIST"
    SYNC = "SYNC"
    GPS = "GPS"

class GUIState():
    def __init__(self, name: StateNames, next_state: StateNames, ok_action=None, fetch_state_data=None):
        self.name = name
        self.next_state = next_state
        self.ok_callback = ok_action
        self.state_data = None
        self.fetch_state_data = fetch_state_data

    def update_state_data(self):
        if self.fetch_state_data is not None:
            self.state_data = self.fetch_state_data()

    def reset_state_data(self):
        self.state_data = None

    def run_ok_action(self):
        if callable(self.ok_callback):
            self.ok_callback()

class GUIManager:
    def __init__(self, start_state: StateNames = StateNames.START, list_page: int = 1, backend=None, clear=False):
        self.device = create_device(backend=backend, clear=clear)
        self.page_size = 4
        self.list_page = max(1, int(list_page or 1))
        self.data_provider = DataProvider(DB_PATH)
        self.live_analyzation_active = False
        self.screen_reset_timer = None

        self.states = {
            StateNames.START: GUIState(StateNames.START, StateNames.LIVE_ANALYZE, self.refresh_start_screen_data, self.data_provider.fetch_initial_state_data),
            StateNames.ANALYZE_RESULT: GUIState(StateNames.ANALYZE_RESULT, None, None, None),
            StateNames.LIVE_ANALYZE: GUIState(
                StateNames.LIVE_ANALYZE,
                StateNames.LIST,
                self.switch_live_analyze,
                lambda: {"live_analyze_active": self.live_analyzation_active},
            ),
            StateNames.LIST: GUIState(StateNames.LIST, StateNames.SYNC, self.next_list_page, lambda: self.data_provider.fetch_list_state_data(self.list_page)),
            StateNames.SYNC: GUIState(StateNames.SYNC, StateNames.GPS, self.start_sync, self.data_provider.fetch_sync_state_data),
            StateNames.GPS: GUIState(StateNames.GPS, StateNames.START, self.switch_gps_state, self.data_provider.fetch_gps_state_data),
        }
        self.current_state = self.states[start_state]
        self.last_detected_bird = None
        self.button_input_handler = None

        self.start()

        try:
            self.button_input_handler = ButtonInputHandler(self)
        except Exception as exc:
            print(f"Button input unavailable: {exc}")

        # threading.Thread(target=KeyboardInputHandler(self).run, daemon=True).start()

    def render_current_state(self) -> None:
        self.current_state.update_state_data()
        render(self.device, self.current_state.state_data, self.current_state.name)

    def start(self) -> None:
        self.render_current_state()

    def handle_ok(self) -> None:
        self.current_state.run_ok_action()
        self.render_current_state()

    def handle_next(self) -> None:
        if self.current_state.next_state is None:
            return
        
        # Deactivate live analyze mode if we are leaving it
        if self.current_state.name == StateNames.LIVE_ANALYZE:
            self.live_analyzation_active = False

        self.current_state = self.states[self.current_state.next_state]
        self.render_current_state()

    def refresh_start_screen_data(self) -> None:
        self.current_state.reset_state_data()
        self.render_current_state()

    def switch_live_analyze(self) -> None:
        self.live_analyzation_active = not self.live_analyzation_active

    def next_list_page(self) -> None:
        total_pages = self.data_provider.get_list_total_pages(self.page_size)
        self.list_page = 1 if self.list_page >= total_pages else self.list_page + 1

    def start_sync(self) -> None:
        # In a real implementation, this would trigger the backend to start syncing data with the server.
        pass

    def switch_gps_state(self) -> None:
        # In a real implementation, this would toggle the GPS state in the backend and fetch updated data for the GPS screen.
        pass

    def render_live_analyze_result(self, detections) -> None:
        if not self.live_analyzation_active:
            return
        
        most_confident_detection = None
        for detection in detections:
            if most_confident_detection is None or detection.confidence > most_confident_detection.confidence:
                most_confident_detection = detection

        state_data = {
            "bird_common_name": most_confident_detection.common_name if most_confident_detection else "No detections",
            "bird_scientific_name": most_confident_detection.scientific_name if most_confident_detection else "",
            "confidence": most_confident_detection.confidence if most_confident_detection else 0.0,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), 
        }

        render(self.device, state_data, StateNames.ANALYZE_RESULT)

        # Reset screen
        if self.screen_reset_timer is not None:
            self.screen_reset_timer.cancel()

        self.screen_reset_timer = threading.Timer(4.0, self.render_current_state)
        self.screen_reset_timer.daemon = True
        self.screen_reset_timer.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="BirdNET-Pi GUI test renderer")
    parser.add_argument("--backend", choices=["auto", "emulator", "waveshare"], default=os.getenv("GUI_BACKEND", "auto"))
    parser.add_argument("--screen", choices=["start", "analyze_result", "live_analyze", "sync", "gps", "list"], default="start")
    parser.add_argument("--list-page", type=int, default=1, help="Static page number for the My Birds screen")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear the e-paper display before rendering")
    parser.add_argument("--clear", action="store_true", help="Clear the e-paper display")
    args = parser.parse_args()

    start_state = StateNames[args.screen.upper()]
    manager = GUIManager(start_state=start_state, list_page=args.list_page, backend=args.backend, clear=not args.no_clear)

    device = manager.device

    if args.clear and hasattr(device, "clear") and getattr(device, "backend", "") == "waveshare":
        device.clear()
        time.sleep(2)
        device.sleep()
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        device.sleep()

if __name__ == "__main__":
    main()