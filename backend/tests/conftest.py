import os
import sys
from pathlib import Path

import pytest


os.environ["LLM_ENABLED"] = "false"

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def pytest_configure(config):
    config.addinivalue_line("markers", "anyio: run async tests with AnyIO")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def isolate_runtime_state(tmp_path, monkeypatch):
    """Keep tests independent from local demo runtime files.

    The application stores work orders and the simulation clock under the runtime
    directory. A developer may have the time machine active while running tests,
    so point every test at a temporary store and reset the clock there.
    """
    # 测试始终走文件隔离存储，与本地 .env 是否配置了 MySQL 无关，
    # 避免测试污染真实数据库（或被其残留状态干扰）。
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("WORK_ORDER_FILE", str(tmp_path / "work_orders.json"))
    monkeypatch.setenv("BUDGET_FILE", str(tmp_path / "budgets.json"))

    from app.core.config import get_settings
    from app.services import simulation_service

    get_settings.cache_clear()
    simulation_service.reset()
    yield
    simulation_service.reset()
    get_settings.cache_clear()
