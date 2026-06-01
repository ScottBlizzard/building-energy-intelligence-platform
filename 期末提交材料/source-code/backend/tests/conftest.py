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
