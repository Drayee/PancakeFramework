"""
异步数据库连接管理器
支持 SQLite / PostgreSQL / MySQL 等
"""

import logging
import os

from databases import Database

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    数据库连接管理器 — 封装数据库连接状态

    使用方法:
        manager = DatabaseManager()
        await manager.init("sqlite:///app.db")
        db = manager.get()
        await manager.close()
    """

    def __init__(self):
        self._database: Database | None = None
        self._url: str | None = None
        self._kwargs: dict = {}

    async def init(self, url: str, **kwargs) -> Database:
        """初始化数据库连接"""
        self._url = url
        self._kwargs = kwargs.copy()

        # SQLite: 确保目录存在，不传连接池参数
        if url.startswith("sqlite"):
            db_path = url.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            kwargs.pop("min_size", None)
            kwargs.pop("max_size", None)

        self._database = Database(url, **kwargs)
        await self._database.connect()
        logger.info(f"数据库已连接: {url.split('@')[-1] if '@' in url else url}")
        return self._database

    async def ping(self) -> bool:
        """健康检查 — 测试数据库连接是否可用"""
        if self._database is None:
            return False
        try:
            await self._database.execute("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"数据库健康检查失败: {e}")
            return False

    async def reconnect(self) -> Database:
        """自动重连 — 断开旧连接并重新建立"""
        if self._url is None:
            raise RuntimeError("数据库未初始化，无法重连")
        logger.info("正在重新连接数据库...")
        await self.close()
        return await self.init(self._url, **self._kwargs)

    async def get_or_reconnect(self) -> Database:
        """获取连接，如果断开则自动重连"""
        if self._database is None:
            if self._url is None:
                raise RuntimeError("数据库未初始化，请先调用 init_database()")
            return await self.reconnect()
        if not await self.ping():
            return await self.reconnect()
        return self._database

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._database:
            await self._database.disconnect()
            logger.info("数据库已断开")
            self._database = None

    def get(self) -> Database:
        """获取当前数据库实例"""
        if self._database is None:
            raise RuntimeError("数据库未初始化，请先调用 init_database()")
        return self._database

    def reset(self) -> None:
        """重置引用（仅用于测试，不断开连接）。生产环境请用 close()"""
        self._database = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 向后兼容的模块级默认实例
_manager = DatabaseManager()

init_database = _manager.init
close_database = _manager.close
get_database = _manager.get
ping_database = _manager.ping
reconnect_database = _manager.reconnect


def create_manager() -> DatabaseManager:
    """创建新的独立管理器（用于测试）"""
    return DatabaseManager()
