import sys
import os
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from typing import Any

if __package__ is None or __package__ == "":
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from gui.data_provider import DataProvider
else:
    from ..data_provider import DataProvider


_REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = os.environ.get("BIRDNET_DB_PATH", str(_REPO_ROOT / "scripts" / "birds.db"))
AUDIO_DIR = os.environ.get("BIRDNET_AUDIO_DIR", str(_REPO_ROOT / ".." / "BirdSongs" / "Extracted" / "By_Date"))
log = logging.getLogger(__name__)


class APIManager:
    def __init__(self, host: str = "0.0.0.0", port: int = 2026, allowed_origins: list[str] | None = None, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        self.db_path = DB_PATH
        db_path_obj = Path(self.db_path)
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        if not db_path_obj.is_file():
            log.warning("Database file not found, creating empty SQLite DB at %s", self.db_path)

        self.data_provider = DataProvider(self.db_path)
        self.app = FastAPI(title="BirdNET-Pi GUI API", debug=debug)

        self._configure_cors(allowed_origins)
        self._register_routes()
        self.running = True

    def _configure_cors(self, allowed_origins: list[str] | None = None) -> None:
        origins = [
            "https://antonrauchenberger.github.io",
            "http://localhost:5173",
            "https://192-168-4-1.sslip.io",
        ]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_routes(self) -> None:
        @self.app.get("/device/details")
        async def get_device_details() -> dict:
            return self.data_provider.get_device_details()
        
        @self.app.get("/device/settings", response_model=None)
        async def get_device_settings() -> dict | None:
            settings = self.data_provider.get_device_settings()
            if settings is None:
                return Response(status_code=204)
            return settings
        
        @self.app.put("/device/settings", response_model=None)
        async def update_device_settings(new_settings: dict) -> None:
            self.data_provider.update_device_settings(new_settings)

        @self.app.get("/device/benchmarking/reports", response_model=None)
        async def get_device_benchmark_reports() -> dict | None:
            reports = self.data_provider.get_device_benchmark_reports()
            if reports is None:
                return Response(status_code=204)
            return reports
        
        @self.app.post("/device/benchmarking/start", response_model=None)
        async def start_device_benchmarking() -> None:
            self.data_provider.start_device_benchmarking()
            return Response(status_code=202)

        @self.app.get("/latestdetections")
        async def get_latest(limit: int = Query(default=20, ge=1, le=500)) -> list[Any]:
            return self.data_provider.get_latest_bird_detections(limit=limit)
        
        @self.app.get("/sync/pendingdetectionsamount")
        async def get_sync_pending_detections_amount() -> dict:
            pending_detections_amount, pending_species_amount = self.data_provider.get_sync_pending_detections_amount()

            return {"detectionsAmount": pending_detections_amount, "speciesAmount": pending_species_amount}

        @self.app.get("/sync/data")
        async def get_sync_data(offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=500)) -> list[Any]:
            return self.data_provider.get_sync_data(offset=offset, limit=limit)
        
        @self.app.delete("/sync/deletesynceddata")
        async def delete_synced_data() -> dict:
            self.data_provider.delete_synced_data()
            return {"status": "success"}

        @self.app.get("/sync/audiofile", response_model=None)
        async def get_audio_file_for_species(species_com_name: str = Query(..., description="Common name of the species")) -> FileResponse | Response:
            audio_file = self.data_provider.get_audio_file(AUDIO_DIR, species_com_name)
            if audio_file is None:
                return Response(status_code=204)
            return audio_file
        

    def run(self, host: str = "0.0.0.0", port: int = 2026) -> None:
        log.info("Starting GUI API on %s:%s using DB %s", host, port, self.db_path)

        if self.debug:
            # Show detailed server/application logs during local debugging.
            logging.getLogger("uvicorn").setLevel(logging.DEBUG)
            logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
            logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
            logging.getLogger("fastapi").setLevel(logging.DEBUG)

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="debug" if self.debug else "info",
            access_log=True,
            use_colors=self.debug,
        )


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 2026

    api_manager = APIManager(host, port, debug=True)
    api_manager.run(host, port)