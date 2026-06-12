"""初始化数据库：建表 + 导入能耗数据集。

用法（先配置好 DATABASE_URL，例如在 .env 中）::

    cd backend
    python -m app.db.init_db

幂等：业务表（work_orders / budgets / sim_state）若已存在则跳过；
energy_readings 默认整表重建（--keep-readings 可保留）。
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from app.core.config import get_settings
from app.db.engine import get_engine, is_db_enabled
from app.db.models import Base
from app.db.repository import has_energy_readings


def _load_energy_readings(engine, *, keep: bool) -> int:
    if keep and has_energy_readings():
        frame = pd.read_sql("SELECT COUNT(*) AS n FROM energy_readings", engine)
        return int(frame.iloc[0]["n"])

    settings = get_settings()
    if not settings.data_file.exists():
        raise FileNotFoundError(f"数据集不存在：{settings.data_file}")

    frame = pd.read_csv(settings.data_file)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame.to_sql(
        "energy_readings",
        engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi",
    )
    return len(frame)


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 MySQL 数据库")
    parser.add_argument(
        "--keep-readings",
        action="store_true",
        help="若 energy_readings 已有数据则不重建",
    )
    args = parser.parse_args()

    if not is_db_enabled():
        print("DATABASE_URL 未配置，数据库未启用。请在 .env 中设置后重试。")
        return 1

    engine = get_engine()
    print(f"连接数据库：{engine.url}")

    Base.metadata.create_all(engine)
    print("业务表已就绪：work_orders / budgets / sim_state")

    count = _load_energy_readings(engine, keep=args.keep_readings)
    print(f"energy_readings 就绪，共 {count} 行。")
    print("初始化完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
