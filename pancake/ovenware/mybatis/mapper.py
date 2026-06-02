"""
MyBatis Plus 风格 Mapper
- BaseMapper: 内置 CRUD，无需写 SQL
- @Mapper: 标记 Mapper 类
- @Select/@Insert/@Update/@Delete: 自定义 SQL
"""

import functools
import inspect
import logging
import re
from dataclasses import dataclass, fields, is_dataclass

from .connection import get_database
from .sql_parser import parse_sql
from .wrapper import QueryWrapper, UpdateWrapper

logger = logging.getLogger(__name__)

_IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def _validate_identifier(name: str, kind: str = "identifier") -> str:
    """Validate SQL identifier to prevent injection."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL {kind}: {name!r}")
    return name

_registered_mappers: dict[str, type] = {}


def _get_table_name(cls) -> str:
    """从类名推断表名：UserMapper -> user, UserInfo -> user_info"""
    name = cls.__name__
    # 去掉 Mapper 后缀
    if name.endswith("Mapper"):
        name = name[:-6]
    # CamelCase -> snake_case
    name = re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', name)
    name = re.sub(r'(?<=[A-Z])([A-Z][a-z])', r'_\1', name)
    return name.lower()


def _get_entity_class(cls) -> type | None:
    """从 Mapper 类的类型注解获取实体类"""
    for base in getattr(cls, '__orig_bases__', ()):
        args = getattr(base, '__args__', ())
        if args:
            return args[0]
    return None


def _row_to_entity(row, entity_cls) -> dataclass:
    """行数据转实体"""
    if row is None:
        return None
    data = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
    if is_dataclass(entity_cls):
        field_names = {f.name for f in fields(entity_cls)}
        filtered = {k: v for k, v in data.items() if k in field_names}
        return entity_cls(**filtered)
    return data


def _rows_to_entities(rows, entity_cls) -> list:
    """多行数据转实体列表"""
    return [_row_to_entity(r, entity_cls) for r in rows]


def _build_where_from_dict(params: dict) -> tuple[str, dict]:
    """从字典构建 WHERE 子句"""
    conditions = []
    values = {}
    for key, val in params.items():
        if val is not None:
            _validate_identifier(key, "column")
            conditions.append(f"{key} = :{key}")
            values[key] = val
    where = " AND ".join(conditions)
    return (" WHERE " + where) if where else "", values


class BaseMapper:
    """
    MyBatis Plus BaseMapper
    提供通用 CRUD 方法，子类自动继承
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 自动推断表名和实体类
        if not hasattr(cls, '_table_name'):
            cls._table_name = _get_table_name(cls)
        if not hasattr(cls, '_entity_class'):
            cls._entity_class = _get_entity_class(cls)
        # Validate table name at registration time
        _validate_identifier(cls._table_name, "table")
        # 注册
        _registered_mappers[cls.__name__] = cls
        logger.info(f"Mapper {cls.__name__} 已注册 (table={cls._table_name})")

    async def select_by_id(self, id: int):
        """根据 ID 查询"""
        db = get_database()
        sql = f"SELECT * FROM {self._table_name} WHERE id = :id"
        row = await db.fetch_one(query=sql, values={"id": id})
        return _row_to_entity(row, self._entity_class)

    async def select_list(self, **kwargs):
        """条件查询列表"""
        db = get_database()
        where, values = _build_where_from_dict(kwargs)
        sql = f"SELECT * FROM {self._table_name}{where}"
        rows = await db.fetch_all(query=sql, values=values)
        return _rows_to_entities(rows, self._entity_class)

    async def select_one(self, **kwargs):
        """条件查询单条"""
        db = get_database()
        where, values = _build_where_from_dict(kwargs)
        sql = f"SELECT * FROM {self._table_name}{where} LIMIT 1"
        row = await db.fetch_one(query=sql, values=values)
        return _row_to_entity(row, self._entity_class)

    async def select_count(self, **kwargs) -> int:
        """条件计数"""
        db = get_database()
        where, values = _build_where_from_dict(kwargs)
        sql = f"SELECT COUNT(*) as cnt FROM {self._table_name}{where}"
        row = await db.fetch_one(query=sql, values=values)
        return row["cnt"] if row else 0

    async def insert(self, **kwargs) -> int:
        """插入数据，返回 lastrowid"""
        db = get_database()
        for k in kwargs:
            _validate_identifier(k, "column")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(f":{k}" for k in kwargs.keys())
        sql = f"INSERT INTO {self._table_name} ({cols}) VALUES ({placeholders})"
        return await db.execute(query=sql, values=kwargs)

    async def insert_batch(self, records: list[dict]) -> int:
        """批量插入，返回插入的记录数"""
        if not records:
            return 0
        db = get_database()
        for k in records[0]:
            _validate_identifier(k, "column")
        cols = ", ".join(records[0].keys())
        placeholders = ", ".join(f":{k}" for k in records[0].keys())
        sql = f"INSERT INTO {self._table_name} ({cols}) VALUES ({placeholders})"
        for record in records:
            await db.execute(query=sql, values=record)
        return len(records)

    async def update_by_id(self, id: int, **kwargs) -> int:
        """根据 ID 更新"""
        db = get_database()
        for k in kwargs:
            _validate_identifier(k, "column")
        set_parts = ", ".join(f"{k} = :{k}" for k in kwargs.keys())
        kwargs["__id"] = id
        sql = f"UPDATE {self._table_name} SET {set_parts} WHERE id = :__id"
        return await db.execute(query=sql, values=kwargs)

    async def delete_by_id(self, id: int) -> int:
        """根据 ID 删除"""
        db = get_database()
        sql = f"DELETE FROM {self._table_name} WHERE id = :id"
        return await db.execute(query=sql, values={"id": id})

    async def delete_batch_by_ids(self, ids: list) -> int:
        """批量删除"""
        if not ids:
            return 0
        db = get_database()
        placeholders = ", ".join(f":id_{i}" for i in range(len(ids)))
        values = {f"id_{i}": id for i, id in enumerate(ids)}
        sql = f"DELETE FROM {self._table_name} WHERE id IN ({placeholders})"
        return await db.execute(query=sql, values=values)

    # ---- QueryWrapper 链式查询 ----

    async def select(self, wrapper: QueryWrapper = None, **kwargs):
        """
        链式条件查询列表

        用法:
            await mapper.select(qw().eq("name", "Alice").ge("age", 18))
            await mapper.select(name="Alice")  # 兼容旧写法
        """
        db = get_database()
        if wrapper is not None:
            sql, values = wrapper.to_select_sql(self._table_name)
        else:
            where, values = _build_where_from_dict(kwargs)
            sql = f"SELECT * FROM {self._table_name}{where}"
        rows = await db.fetch_all(query=sql, values=values)
        return _rows_to_entities(rows, self._entity_class)

    async def select_one(self, wrapper: QueryWrapper = None, **kwargs):
        """
        链式条件查询单条

        用法:
            await mapper.select_one(qw().eq("name", "Alice"))
        """
        db = get_database()
        if wrapper is not None:
            sql, values = wrapper.to_select_sql(self._table_name)
            # 自动加 LIMIT 1（如果没有指定）
            if wrapper._limit is None:
                sql += " LIMIT 1"
        else:
            where, values = _build_where_from_dict(kwargs)
            sql = f"SELECT * FROM {self._table_name}{where} LIMIT 1"
        row = await db.fetch_one(query=sql, values=values)
        return _row_to_entity(row, self._entity_class)

    async def select_count(self, wrapper: QueryWrapper = None, **kwargs) -> int:
        """
        链式条件计数

        用法:
            await mapper.select_count(qw().like("name", "A"))
        """
        db = get_database()
        if wrapper is not None:
            sql, values = wrapper.to_count_sql(self._table_name)
        else:
            where, values = _build_where_from_dict(kwargs)
            sql = f"SELECT COUNT(*) as cnt FROM {self._table_name}{where}"
        row = await db.fetch_one(query=sql, values=values)
        return row["cnt"] if row else 0

    async def update(self, update_wrapper: UpdateWrapper = None, **kwargs) -> int:
        """
        链式条件更新

        用法:
            await mapper.update(UpdateWrapper().set("name", "Bob").eq("id", 1))
            await mapper.update(UpdateWrapper().set("name", "Bob"), id=1)  # 条件用 kwargs
        """
        db = get_database()
        if update_wrapper is not None:
            sql, values = update_wrapper.to_update_sql(self._table_name)
        else:
            raise ValueError("必须提供 UpdateWrapper")
        return await db.execute(query=sql, values=values)

    async def delete(self, wrapper: QueryWrapper = None, **kwargs) -> int:
        """
        链式条件删除

        用法:
            await mapper.delete(qw().lt("age", 18))
            await mapper.delete(age=18)  # 兼容旧写法
        """
        db = get_database()
        if wrapper is not None:
            where_clause, values = wrapper.to_where_clause()
            sql = f"DELETE FROM {self._table_name}{where_clause}"
        else:
            where, values = _build_where_from_dict(kwargs)
            sql = f"DELETE FROM {self._table_name}{where}"
        return await db.execute(query=sql, values=values)


def Mapper(cls):
    """@Mapper 装饰器：将类标记为 Mapper 并注入 BaseMapper 方法"""
    # 注入 BaseMapper 的所有方法
    for name, method in inspect.getmembers(BaseMapper, predicate=inspect.isfunction):
        if not name.startswith('_') and not hasattr(cls, name):
            setattr(cls, name, method)

    # 设置表名和实体类
    if not hasattr(cls, '_table_name'):
        cls._table_name = _get_table_name(cls)
    if not hasattr(cls, '_entity_class'):
        cls._entity_class = _get_entity_class(cls)

    _validate_identifier(cls._table_name, "table")
    _registered_mappers[cls.__name__] = cls
    logger.info(f"Mapper {cls.__name__} 已注册 (table={cls._table_name})")
    return cls

Mapper._load_priority = 10  # Mapper 优先加载（controller 默认 50）


def Select(sql: str):
    """自定义查询装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db = get_database()
            params = _extract_params(func, args, kwargs)
            parsed_sql, bound_params = parse_sql(sql, params)
            rows = await db.fetch_all(query=parsed_sql, values=bound_params)
            return_type = _get_return_type(func)
            if return_type and return_type is not list:
                from dataclasses import is_dataclass
                if is_dataclass(return_type):
                    return [_row_to_entity(r, return_type) for r in rows]
            return [dict(r._mapping) if hasattr(r, '_mapping') else dict(r) for r in rows]
        wrapper._mybatis_sql = sql
        return wrapper
    return decorator


def SelectOne(sql: str):
    """自定义单条查询装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db = get_database()
            params = _extract_params(func, args, kwargs)
            parsed_sql, bound_params = parse_sql(sql, params)
            row = await db.fetch_one(query=parsed_sql, values=bound_params)
            if row is None:
                return None
            return_type = _get_return_type(func)
            if return_type and is_dataclass(return_type):
                return _row_to_entity(row, return_type)
            return dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
        wrapper._mybatis_sql = sql
        return wrapper
    return decorator


def Insert(sql: str):
    """自定义插入装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db = get_database()
            params = _extract_params(func, args, kwargs)
            parsed_sql, bound_params = parse_sql(sql, params)
            return await db.execute(query=parsed_sql, values=bound_params)
        wrapper._mybatis_sql = sql
        return wrapper
    return decorator


def Update(sql: str):
    """自定义更新装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db = get_database()
            params = _extract_params(func, args, kwargs)
            parsed_sql, bound_params = parse_sql(sql, params)
            return await db.execute(query=parsed_sql, values=bound_params)
        wrapper._mybatis_sql = sql
        return wrapper
    return decorator


def Delete(sql: str):
    """自定义删除装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db = get_database()
            params = _extract_params(func, args, kwargs)
            parsed_sql, bound_params = parse_sql(sql, params)
            return await db.execute(query=parsed_sql, values=bound_params)
        wrapper._mybatis_sql = sql
        return wrapper
    return decorator


def _get_return_type(func):
    sig = inspect.signature(func)
    return_type = sig.return_annotation
    if return_type is inspect.Parameter.empty:
        return None
    origin = getattr(return_type, "__origin__", None)
    if origin is list:
        args = getattr(return_type, "__args__", ())
        return args[0] if args else None
    return return_type


def _extract_params(func, args, kwargs) -> dict:
    sig = inspect.signature(func)
    params = {}
    param_names = list(sig.parameters.keys())
    start = 1 if param_names and param_names[0] == "self" else 0
    for i, arg in enumerate(args[start:]):
        idx = i + start
        if idx < len(param_names):
            params[param_names[idx]] = arg
    params.update(kwargs)
    for name in param_names[start:]:
        if name not in params:
            param = sig.parameters[name]
            if param.default is not inspect.Parameter.empty:
                params[name] = param.default
    return params


def get_registered_mappers() -> dict[str, type]:
    return _registered_mappers.copy()
