"""
数据库迁移工具
- 基于 Mapper dataclass 自动对比表结构
- 版本管理: _migrations 表记录已执行的迁移
- 支持 add_column / create_table
"""

import logging
from dataclasses import fields, is_dataclass
from datetime import datetime

from .connection import get_database
from .mapper import _validate_identifier

logger = logging.getLogger(__name__)


class Migration:
    """单条迁移"""

    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self._steps: list = []

    def create_table(self, table_name: str, entity_class: type) -> "Migration":
        """创建表"""
        if not is_dataclass(entity_class):
            raise ValueError(f"{entity_class} 不是 dataclass")
        self._steps.append(("create_table", table_name, entity_class))
        return self

    def add_column(self, table_name: str, column_name: str, column_type: str) -> "Migration":
        """添加列"""
        self._steps.append(("add_column", table_name, column_name, column_type))
        return self

    def drop_table(self, table_name: str) -> "Migration":
        """删除表"""
        self._steps.append(("drop_table", table_name))
        return self

    def raw_sql(self, sql: str) -> "Migration":
        """执行原始 SQL"""
        self._steps.append(("raw_sql", sql))
        return self


class MigrationManager:
    """迁移管理器"""

    def __init__(self):
        self._migrations: list[Migration] = []

    def register(self, migration: Migration) -> None:
        """注册迁移"""
        self._migrations.append(migration)
        self._migrations.sort(key=lambda m: m.version)

    async def _ensure_migration_table(self) -> None:
        """确保 _migrations 表存在"""
        db = get_database()
        await db.execute(query="""
            CREATE TABLE IF NOT EXISTS _migrations (
                version TEXT PRIMARY KEY,
                description TEXT,
                applied_at TEXT
            )
        """)

    async def _get_applied_versions(self) -> set[str]:
        """获取已执行的版本号"""
        db = get_database()
        rows = await db.fetch_all("SELECT version FROM _migrations")
        return {row["version"] for row in rows}

    async def _record_migration(self, migration: Migration) -> None:
        """记录迁移已执行"""
        db = get_database()
        await db.execute(
            "INSERT INTO _migrations (version, description, applied_at) VALUES (:v, :d, :t)",
            {"v": migration.version, "d": migration.description, "t": datetime.now().isoformat()}
        )

    async def migrate(self) -> int:
        """执行所有待执行的迁移，返回执行数量"""
        await self._ensure_migration_table()
        applied = await self._get_applied_versions()
        count = 0

        for migration in self._migrations:
            if migration.version in applied:
                continue

            logger.info(f"执行迁移 {migration.version}: {migration.description}")
            db = get_database()

            try:
                async with db.transaction():
                    for step in migration._steps:
                        await self._execute_step(db, step)
                    await self._record_migration(migration)
                count += 1
                logger.info(f"迁移 {migration.version} 完成")
            except Exception as e:
                logger.error(f"迁移 {migration.version} 失败: {e}")
                raise

        if count == 0:
            logger.info("没有待执行的迁移")
        else:
            logger.info(f"共执行 {count} 个迁移")
        return count

    async def _execute_step(self, db, step: tuple) -> None:
        """执行单个迁移步骤"""
        action = step[0]

        if action == "create_table":
            _, table_name, entity_class = step
            _validate_identifier(table_name, "table")
            from .mapper import BaseMapper
            cols = []
            for f in fields(entity_class):
                col_type = BaseMapper._TYPE_MAP.get(f.type, "TEXT")
                if f.name == "id":
                    cols.append(f"    {f.name} INTEGER PRIMARY KEY AUTOINCREMENT")
                else:
                    cols.append(f"    {f.name} {col_type}")
            col_sql = ",\n".join(cols)
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n{col_sql}\n)"
            await db.execute(query=sql)

        elif action == "add_column":
            _, table_name, column_name, column_type = step
            _validate_identifier(table_name, "table")
            _validate_identifier(column_name, "column")
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            await db.execute(query=sql)

        elif action == "drop_table":
            _, table_name = step
            _validate_identifier(table_name, "table")
            await db.execute(query=f"DROP TABLE IF EXISTS {table_name}")

        elif action == "raw_sql":
            _, sql = step
            await db.execute(query=sql)

    async def status(self) -> list[dict]:
        """查看迁移状态"""
        await self._ensure_migration_table()
        applied = await self._get_applied_versions()
        result = []
        for m in self._migrations:
            result.append({
                "version": m.version,
                "description": m.description,
                "applied": m.version in applied,
            })
        return result


# 模块级默认实例
_manager = MigrationManager()

register_migration = _manager.register
run_migrations = _manager.migrate
migration_status = _manager.status
