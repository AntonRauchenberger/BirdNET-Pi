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
from data_provider import DataProvider

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
    def __init__(self, device, start_state: StateNames = StateNames.START, list_page: int = 1):
        self.device = device
        self.page_size = 4
        self.list_page = max(1, int(list_page or 1))
        self.data_provider = DataProvider()

        self.states = {
            StateNames.START: GUIState(StateNames.START, StateNames.LIST, None, self.data_provider.fetch_initial_state_data),
            StateNames.ANALYZE: GUIState(StateNames.ANALYZE, None, None, self.data_provider.fetch_analyze_state_data),
            StateNames.LIST: GUIState(StateNames.LIST, StateNames.SYNC, self.next_list_page, lambda: self.data_provider.fetch_list_state_data(self.list_page)),
            StateNames.SYNC: GUIState(StateNames.SYNC, StateNames.GPS, self.start_sync, self.data_provider.fetch_sync_state_data),
            StateNames.GPS: GUIState(StateNames.GPS, StateNames.START, self.switch_gps_state, self.data_provider.fetch_gps_state_data),
        }
        self.current_state = self.states[start_state]
        self.last_detected_bird = None

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
        self.current_state = self.states[self.current_state.next_state]
        self.render_current_state()

    def next_list_page(self) -> None:
        total_pages = self.data_provider.get_list_total_pages(self.page_size)
        self.list_page = 1 if self.list_page >= total_pages else self.list_page + 1

    def start_sync(self) -> None:
        # In a real implementation, this would trigger the backend to start syncing data with the server.
        pass

    def switch_gps_state(self) -> None:
        # In a real implementation, this would toggle the GPS state in the backend and fetch updated data for the GPS screen.
        pass

def main() -> None:
    parser = argparse.ArgumentParser(description="BirdNET-Pi GUI test renderer")
    parser.add_argument("--backend", choices=["auto", "emulator", "waveshare"], default=os.getenv("GUI_BACKEND", "auto"))
    parser.add_argument("--screen", choices=["start", "analyze", "sync", "gps", "list"], default="list")
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
    main()