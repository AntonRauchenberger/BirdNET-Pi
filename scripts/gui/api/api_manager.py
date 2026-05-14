import sys
import os
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Any

if __package__ is None or __package__ == "":
    gui_dir = Path(__file__).resolve().parent.parent
    if str(gui_dir) not in sys.path:
        sys.path.insert(0, str(gui_dir))

    from data_provider import DataProvider
else:
    from ..data_provider import DataProvider


_REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = os.environ.get("BIRDNET_DB_PATH", str(_REPO_ROOT / "scripts" / "birds.db"))


class APIManager:
    def __init__(self, host: str = "0.0.0.0", port: int = 2026, allowed_origins: list[str] | None = None, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        self.db_path = DB_PATH
        if not Path(self.db_path).is_file():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        self.data_provider = DataProvider(self.db_path)
        self.app = FastAPI(title="BirdNET-Pi GUI API", debug=debug)

        self._configure_cors(allowed_origins)
        self._register_routes()

        self.run(host=host, port=port)
        self.running = True

    def _configure_cors(self, allowed_origins: list[str] | None = None) -> None:
        # TODO adjust allowed origins for better security in real deployment
        origins = allowed_origins or ["*"]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_routes(self) -> None:
        @self.app.get("/device/details")
        async def get_device_details() -> dict:
            return self.data_provider.get_device_details()

        @self.app.get("/latestdetections")
        async def get_latest(limit: int = Query(default=20, ge=1, le=500)) -> list[Any]:
            return self.data_provider.get_latest_bird_detections(limit=limit)
        
        @self.app.get("/sync/pendingdetectionsamount")
        async def get_sync_pending_detections_amount() -> dict:
            return {"amount": self.data_provider.get_sync_pending_detections_amount()}

        @self.app.get("/sync/data")
        async def get_sync_data(offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=500)) -> list[Any]:
            return self.data_provider.get_sync_data(offset=offset, limit=limit)
        
        @self.app.delete("/sync/deletesynceddata")
        async def delete_synced_data() -> dict:
            self.data_provider.delete_synced_data()
            return {"status": "success"}
        

    def run(self, host: str = "0.0.0.0", port: int = 2026) -> None:
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