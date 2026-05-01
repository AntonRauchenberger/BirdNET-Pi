"""
Provides state data for the GUI screens.
"""

import os


class DataProvider:
    def fetch_initial_state_data(self) -> dict:
        return {
            "last_detected_bird": "Common chaffinch",
            "last_detected_confidence": "87",
            "total_detections": "148",
            "active since_date": "2024-06-01",
            "active since_days": "23",
            "system_name": "BirdNET-Pi-01",
        }

    def fetch_analyze_state_data(self) -> dict:
        # In a real implementation, this would fetch the latest detection result from the backend.
        return {
            "bird_common_name": "Common chaffinch",
            "bird_scientific_name": "Fringilla coelebs",
            "confidence": 0.85,
            "timestamp": "2024-06-01 12:34:56",
        }
    
    def fetch_live_analyze_state_data(self) -> dict:
        # In a real implementation, this would fetch the current live analyze status and latest detection from the backend.
        return {
            "live_analyze_active": True,
        }

    def fetch_list_state_data(self, current_page: int = 1) -> dict:
        # In a real implementation, this would fetch the list of detected birds from the backend.
        return {
            "current_page": current_page,
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
                {"common_name": "Common starling", "scientific_name": "Sturnus vulgaris", "amount": 3},
            ],
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
