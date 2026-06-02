"""
数据库方言 — 处理 SQLite / PostgreSQL / MySQL 的差异
- 类型映射
- 分页语法
- 自增语法
- 引号风格
"""

import logging

logger = logging.getLogger(__name__)


class Dialect:
    """数据库方言基类"""

    name: str = "generic"

    # Python 类型 -> SQL 类型
    TYPE_MAP: dict[type, str] = {
        int: "INTEGER",
        str: "TEXT",
        float: "REAL",
        bool: "INTEGER",
    }

    def auto_increment(self) -> str:
        return "AUTOINCREMENT"

    def limit_offset(self, limit: int, offset: int) -> str:
        return f"LIMIT {limit} OFFSET {offset}"

    def quote(self, name: str) -> str:
        return name

    def placeholder(self, name: str) -> str:
        return f":{name}"

    def create_table_sql(self, table_name: str, columns: list[str]) -> str:
        col_sql = ",\n".join(columns)
        return f"CREATE TABLE IF NOT EXISTS {self.quote(table_name)} (\n{col_sql}\n)"


class SQLiteDialect(Dialect):
    name = "sqlite"

    TYPE_MAP = {
        int: "INTEGER",
        str: "TEXT",
        float: "REAL",
        bool: "INTEGER",
    }

    def auto_increment(self) -> str:
        return "AUTOINCREMENT"


class PostgreSQLDialect(Dialect):
    name = "postgresql"

    TYPE_MAP = {
        int: "INTEGER",
        str: "VARCHAR(255)",
        float: "DOUBLE PRECISION",
        bool: "BOOLEAN",
    }

    def auto_increment(self) -> str:
        return "SERIAL"

    def quote(self, name: str) -> str:
        return f'"{name}"'


class MySQLDialect(Dialect):
    name = "mysql"

    TYPE_MAP = {
        int: "INT",
        str: "VARCHAR(255)",
        float: "DOUBLE",
        bool: "TINYINT(1)",
    }

    def auto_increment(self) -> str:
        return "AUTO_INCREMENT"

    def quote(self, name: str) -> str:
        return f"`{name}`"


# URL 前缀 -> 方言类
_DIALECT_MAP: dict[str, type] = {
    "sqlite": SQLiteDialect,
    "postgresql": PostgreSQLDialect,
    "postgres": PostgreSQLDialect,
    "mysql": MySQLDialect,
    "mariadb": MySQLDialect,
}


def get_dialect(url: str) -> Dialect:
    """根据数据库 URL 获取对应的方言实例"""
    for prefix, cls in _DIALECT_MAP.items():
        if url.startswith(prefix):
            return cls()
    logger.warning(f"未识别的数据库类型: {url.split(':')[0]}，使用默认方言")
    return Dialect()
