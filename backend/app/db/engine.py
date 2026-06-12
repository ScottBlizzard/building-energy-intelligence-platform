from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def is_db_enabled() -> bool:
    """是否启用数据库持久化（由 DATABASE_URL 是否配置决定）。"""
    return bool(get_settings().database_url)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    url = get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL 未配置，数据库未启用。")
    # pool_pre_ping 避免 MySQL 连接被服务端回收后报 "server has gone away"。
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600, future=True)


@lru_cache(maxsize=1)
def _session_factory():
    return sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)


def get_session() -> Session:
    return _session_factory()()


def reset_engine_cache() -> None:
    """清空引擎/会话缓存（切换 DATABASE_URL 或测试时使用）。"""
    get_engine.cache_clear()
    _session_factory.cache_clear()
