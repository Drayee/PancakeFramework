"""测试类型转换装饰器：@service, @configuration, @function, @struct"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pancake.dough import Dough, DoughMeta, Scope
from pancake.decorators import service, configuration, function, struct
from pancake.base.service import Service
from pancake.base.configuration import Configuration
from pancake.base.function import Function
from dataclasses import fields


# ---- 测试 @service ----

def test_service_decorator():
    """@service 将普通类转换为 Service 子类"""
    @service
    class UserService:
        def get_user(self):
            return "user"

    assert issubclass(UserService, Service)
    assert issubclass(UserService, Dough)
    assert isinstance(UserService, DoughMeta)
    assert UserService._dough_type == "service"
    print("[OK] @service 装饰器正常")


def test_service_already_service():
    """已经是 Service 的类不重复转换"""
    class MyService(Service):
        pass

    result = service(MyService)
    assert result is MyService
    print("[OK] @service 已是 Service 时跳过")


# ---- 测试 @configuration ----

def test_configuration_decorator():
    """@configuration 将普通类转换为 Configuration 子类"""
    @configuration
    class AppConfig:
        def setup(self):
            pass

    assert issubclass(AppConfig, Configuration)
    assert issubclass(AppConfig, Dough)
    assert AppConfig._dough_type == "configuration"
    print("[OK] @configuration 装饰器正常")


# ---- 测试 @function ----

def test_function_decorator():
    """@function 将函数转换为 Function 子类"""
    @function
    def get_data(name: str) -> str:
        return f"data: {name}"

    # 应该返回一个类，而不是函数
    assert isinstance(get_data, type)
    assert issubclass(get_data, Function)
    assert issubclass(get_data, Dough)
    assert get_data._dough_type == "function"

    # 类名应该是 PascalCase
    assert get_data.__name__ == "GetData"

    # 实例应该可以调用
    instance = get_data()
    result = instance("test")
    assert result == "data: test"
    print("[OK] @function 装饰器正常")


def test_function_async():
    """@function 支持 async 函数"""
    @function
    async def async_process(data: str) -> str:
        return f"processed: {data}"

    assert issubclass(async_process, Function)
    assert async_process._dough_type == "function"
    print("[OK] @function async 函数正常")


# ---- 测试 @struct ----

def test_struct_decorator():
    """@struct 将类标记为 dataclass（不注册到 IoC 容器）"""
    @struct
    class UserDTO:
        name: str = ""
        age: int = 0

    # @struct 不再转换为 Struct/Dough 子类，仅应用 @dataclass
    assert UserDTO._dough_type == "struct"

    # 应该有 dataclass 字段
    field_names = [f.name for f in fields(UserDTO)]
    assert "name" in field_names
    assert "age" in field_names

    # 可以创建实例
    user = UserDTO(name="Alice", age=30)
    assert user.name == "Alice"
    assert user.age == 30
    print("[OK] @struct 装饰器正常")


# ---- 测试冲突检测 ----

def test_conflict_service_and_configuration():
    """@service 和 @configuration 不能同时使用"""
    try:
        @service
        @configuration
        class ConflictClass:
            pass
        assert False, "应该抛出 TypeError"
    except TypeError as e:
        assert "已应用" in str(e)
        print("[OK] 冲突检测: @service + @configuration 正确报错")


def test_struct_is_pure_dataclass():
    """@struct 仅标记为 dataclass，不与 @service 冲突"""
    @struct
    class UserDTO:
        name: str = ""
        age: int = 0

    # @struct 只是 dataclass 标记，不注册到 IoC，不与 service 冲突
    assert hasattr(UserDTO, '__dataclass_fields__')
    assert UserDTO._dough_type == "struct"
    print("[OK] @struct 是纯 dataclass 标记")


def test_same_decorator_no_conflict():
    """同一个装饰器重复应用不报错"""
    @service
    class MyService:
        pass

    # 再次应用 @service 不应该报错
    result = service(MyService)
    assert result is MyService
    print("[OK] 同一装饰器重复应用不冲突")


if __name__ == "__main__":
    test_service_decorator()
    test_service_already_service()
    test_configuration_decorator()
    test_function_decorator()
    test_function_async()
    test_struct_decorator()
    test_conflict_service_and_configuration()
    test_struct_is_pure_dataclass()
    test_same_decorator_no_conflict()
    print("\n所有测试通过！")
