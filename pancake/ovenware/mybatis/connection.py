"""
异步数据库连接管理器
支持 SQLite / PostgreSQL / MySQL 等
"""

import logging
import os

from databases import Database

logger = logging.getLogger(__name__)

_database: Database | None = None


async def init_database(url: str, **kwargs) -> Database:
    """初始化数据库连接"""
    global _database

    # SQLite: 确保目录存在，不传连接池参数
    if url.startswith("sqlite"):
        db_path = url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        kwargs.pop("min_size", None)
        kwargs.pop("max_size", None)

    _database = Database(url, **kwargs)
    await _database.connect()
    logger.info(f"数据库已连接: {url.split('@')[-1] if '@' in url else url}")
    return _database


async def close_database():
    """关闭数据库连接"""
    global _database
    if _database:
        await _database.disconnect()
        logger.info("数据库已断开")
        _database = None


def get_database() -> Database:
    """获取当前数据库实例"""
    if _database is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return _database
