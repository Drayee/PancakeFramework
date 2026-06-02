"""
结果映射类型
支持 dict 和 dataclass 自动转换
"""

from dataclasses import fields, is_dataclass
from typing import Any, TypeVar

T = TypeVar("T")


def row_to_dict(row) -> dict:
    """将数据库行转为字典"""
    if isinstance(row, dict):
        return dict(row)
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if hasattr(row, "keys"):
        return {k: row[k] for k in row.keys()}
    return dict(row)


def row_to_dataclass(row, cls: type[T]) -> T:
    """将数据库行转为 dataclass 实例"""
    data = row_to_dict(row)
    field_names = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in data.items() if k in field_names}
    return cls(**filtered)


def map_result(row, result_type: type | None = None) -> Any:
    """映射单行结果"""
    if result_type is None:
        return row_to_dict(row)
    if is_dataclass(result_type):
        return row_to_dataclass(row, result_type)
    if result_type is dict:
        return row_to_dict(row)
    return row


def map_results(rows, result_type: type | None = None) -> list:
    """映射多行结果"""
    return [map_result(row, result_type) for row in rows]
