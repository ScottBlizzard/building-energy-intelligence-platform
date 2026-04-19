import os
from functools import lru_cache
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        self.project_name = "Building Energy Intelligence Platform"
        self.api_v1_prefix = "/api/v1"
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.root_dir = Path(__file__).resolve().parents[3]
        self.data_file = self._resolve_path(
            os.getenv("DATA_FILE", "data/samples/energy_records.csv")
        )
        self.knowledge_base_dir = self._resolve_path(
            os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base")
        )
        self.allowed_origins = [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
            if origin.strip()
        ]

    def _resolve_path(self, raw_path: str) -> Path:
        path = Path(raw_path)
        if path.is_absolute():
            return path
        return self.root_dir / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

