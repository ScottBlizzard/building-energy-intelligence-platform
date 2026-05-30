import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


class Settings:
    def __init__(self) -> None:
        self.project_name = "Building Energy Intelligence Platform"
        self.api_v1_prefix = "/api/v1"
        self.root_dir = Path(__file__).resolve().parents[3]
        load_dotenv(self.root_dir / ".env", override=False)

        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.data_file = self._resolve_path(
            os.getenv("DATA_FILE", "data/samples/energy_records.csv")
        )
        self.knowledge_base_dir = self._resolve_path(
            os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base")
        )
        self.work_order_file = self._resolve_path(
            os.getenv("WORK_ORDER_FILE", "data/runtime/work_orders.json")
        )
        self.allowed_origins = [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
            if origin.strip()
        ]
        self.llm_enabled = os.getenv("LLM_ENABLED", "false").lower() == "true"
        self.llm_provider = os.getenv("LLM_PROVIDER", "local").strip().lower()
        self.llm_base_url = os.getenv("LLM_BASE_URL", "").strip()
        self.llm_api_key = os.getenv("LLM_API_KEY", "").strip()
        self.llm_model = os.getenv("LLM_MODEL", "").strip()
        self.llm_timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "768"))
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.llm_top_p = float(os.getenv("LLM_TOP_P", "0.7"))

    def _resolve_path(self, raw_path: str) -> Path:
        path = Path(raw_path)
        if path.is_absolute():
            return path
        return self.root_dir / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
