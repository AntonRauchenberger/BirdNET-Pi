"""
Controls which screen is active and handles the transition between them.
"""

import argparse
import os
import time

from enum import Enum

from input_handler import InputHandler
from renderer import render
from display_driver import create_device

class StateNames(Enum):
    START = "START"
    ANALYZE = "ANALYZE"
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
    def __init__(self, device, start_state=StateNames.ANALYZE, list_page=1):
        self.device = device
        self.page_size = 4
        self.list_page = max(1, int(list_page or 1))

        self.states = {
            StateNames.START: GUIState(StateNames.START, StateNames.LIST, None, self.fetch_initial_state_data),
            StateNames.ANALYZE: GUIState(StateNames.ANALYZE, None, None, self.fetch_analyze_state_data),
            StateNames.LIST: GUIState(StateNames.LIST, StateNames.SYNC, self.next_list_page, self.fetch_list_state_data),
            StateNames.SYNC: GUIState(StateNames.SYNC, StateNames.GPS, self.start_sync, self.fetch_sync_state_data),
            StateNames.GPS: GUIState(StateNames.GPS, StateNames.START, self.switch_gps_state, self.fetch_gps_state_data),
        }
        self.current_state = self.states[start_state]
        self.last_detected_bird = None

    def render_current_state(self):
        self.current_state.update_state_data()
        render(self.device, self.current_state.state_data, self.current_state.name)

    def start(self):
        self.render_current_state()

    def handle_ok(self):
        self.current_state.run_ok_action()
        self.render_current_state()

    def handle_next(self):
        self.current_state = self.states[self.current_state.next_state]
        self.render_current_state()

    def next_list_page(self):
        total_pages = max(1, (len(self.bird_list) + self.page_size - 1) // self.page_size)
        self.list_page = 1 if self.list_page >= total_pages else self.list_page + 1

    def start_sync(self):
        # In a real implementation, this would trigger the backend to start syncing data with the server.
        pass

    def switch_gps_state(self):
        # In a real implementation, this would toggle the GPS state in the backend and fetch updated data for the GPS screen.
        pass

    def fetch_initial_state_data(self):
        return {}
    
    def fetch_analyze_state_data(self):
        # In a real implementation, this would fetch the latest detection result from the backend.
        return {
            "bird_name": "Common chaffinch (Fringilla coelebs)",
            "bird_image_path": os.path.join(os.path.dirname(__file__), "assets", "images", "birds", "Common chaffinch (Fringilla coelebs).png"),
            "confidence": 0.85,
            "timestamp": "2024-06-01 12:34:56",
        }
    
    def fetch_list_state_data(self):
        # In a real implementation, this would fetch the list of detected birds from the backend, with pagination support.
        return {
            "current_page": 1,
            "bird_list": [
                {"common_name": "Common chaffinch", "scientific_name": "Fringilla coelebs", "amount": 5},
                {"common_name": "European robin", "scientific_name": "Erithacus rubecula", "amount": 3},
                {"common_name": "Great tit", "scientific_name": "Parus major", "amount": 2},
                {"common_name": "Blue tit", "scientific_name": "Cyanistes caeruleus", "amount": 4},
                {"common_name": "Eurasian blackbird", "scientific_name": "Turdus merula", "amount": 1},
                {"common_name": "House sparrow", "scientific_name": "Passer domesticus", "amount": 6},
                {"common_name": "European goldfinch", "scientific_name": "Carduelis carduelis", "amount": 2},
                {"common_name": "Eurasian bluetit", "scientific_name": "Cyanistes caeruleus", "amount": 4},
                {"common_name": "Eurasian blackcap", "scientific_name": "Sylvia atricapilla", "amount": 1},
                {"common_name": "Common starling", "scientific_name": "Sturnus vulgaris", "amount": 3}
            ]
        }

    def fetch_sync_state_data(self):
        # In a real implementation, this would fetch the current sync status from the backend.
        return {
            "wlan_ssid": "MyWiFiNetwork_1",
            "status": "Ready",
            "last_sync": "2024-06-01 12:34:56",
            "entries_to_sync": 42,
        }

    def fetch_gps_state_data(self):
        # In a real implementation, this would fetch the current GPS status and coordinates from the backend.
        return {
            "status": "ON",
            "latitude": "52.5200 N",
            "longitude": "13.4050 E",
            "last_update": "2024-06-01 12:34:56",
        }


def __main__():
    parser = argparse.ArgumentParser(description="BirdNET-Pi GUI test renderer")
    parser.add_argument("--backend", choices=["auto", "emulator", "waveshare"], default=os.getenv("GUI_BACKEND", "auto"))
    parser.add_argument("--screen", choices=["start", "analyze", "sync", "gps", "list"], default="analyze")
    parser.add_argument("--list-page", type=int, default=1, help="Static page number for the My Birds screen")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear the e-paper display before rendering")
    parser.add_argument("--clear", action="store_true", help="Clear the e-paper display")
    args = parser.parse_args()

    device = create_device(backend=args.backend, clear=not args.no_clear)

    if args.clear and hasattr(device, "clear") and getattr(device, "backend", "") == "waveshare":
        device.clear()
        time.sleep(2)
        device.sleep()
        return

    start_state = StateNames[args.screen.upper()]
    manager = GUIManager(device=device, start_state=start_state, list_page=args.list_page)
    manager.start()

    if getattr(device, "backend", "") == "emulator":
        InputHandler(manager).run()
        return

    if getattr(device, "backend", "") == "waveshare":
        # Keep image visible briefly, then put panel to sleep.
        time.sleep(2)
        device.sleep()
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        device.sleep()

if __name__ == "__main__":
    __main__()