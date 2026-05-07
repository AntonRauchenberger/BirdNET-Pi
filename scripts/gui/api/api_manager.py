import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

if __package__ is None or __package__ == "":
    gui_dir = Path(__file__).resolve().parent.parent
    if str(gui_dir) not in sys.path:
        sys.path.insert(0, str(gui_dir))

    from data_provider import DataProvider
else:
    from ..data_provider import DataProvider


_REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = str(_REPO_ROOT / "scripts" / "birds.db")


class APIManager:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000, allowed_origins: list[str] | None = None):
        self.db_path = DB_PATH
        self.data_provider = DataProvider(DB_PATH)
        self.app = FastAPI(title="BirdNET-Pi GUI API")

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
        @self.app.get("/health")
        async def health() -> dict:
            # TODO implement
            return {"status": "ok"}

        @self.app.get("/latestdetections")
        async def get_latest(limit: int = Query(default=20, ge=1, le=500)) -> list[dict]:
            return self.data_provider.get_latest_bird_detections(limit=limit)
        
        @self.app.get("/sync/data")
        async def get_sync_data() -> list[dict]:
            return self.data_provider.get_sync_data()
        
    # TODO add missing routes for other state data

    def run(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        uvicorn.run(self.app, host=host, port=port)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8000

    api_manager = APIManager(host, port)