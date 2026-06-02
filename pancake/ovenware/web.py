"""
    # Web 服务 插件
    提供 Web 服务的构建和运行功能

"""


from fastapi import FastAPI
import uvicorn
import logging
from pancake import oven

logger = logging.getLogger(__name__)

# 检查服务配置文件是否存在
def _check():
    import os
    from pancake.settings import get_path
    yaml_dir = get_path("yaml_dir")
    yaml_path = os.path.join(yaml_dir, "service.yaml")
    yml_path = os.path.join(yaml_dir, "service.yml")
    if not os.path.exists(yaml_path) and not os.path.exists(yml_path):
        logger.error("service.yaml 或 service.yml 文件不存在")
        raise FileNotFoundError("service.yaml 或 service.yml 文件不存在")

"""
     Web 服务 主类
"""
class Main(InitAction):

    def __init__(self):
        oven.pancake_dough["PostController"] = {}
        oven.pancake_dough["GetController"] = {}
        oven.pancake_dough["PostAutoController"] = {}
        oven.pancake_dough["GetAutoController"] = {}
        oven.pancake_other["path"] = {}

        self.service_title = oven.pancake_yaml["service.title"]
        self.service_version = oven.pancake_yaml["service.version"]
        self.service_host = oven.pancake_yaml["service.host"]
        self.service_port = oven.pancake_yaml["service.port"]
        # 构建所有控制器实例
        self.app = FastAPI(title=self.service_title, version=self.service_version)

    @staticmethod
    def check():
        _check()

    def build(self):
        for name, func in oven.pancake_dough["PostController"].items():
            self.app.add_api_route(oven.pancake_other["path"][name], func, methods=["POST"])
        for name, func in oven.pancake_dough["GetController"].items():
            self.app.add_api_route(oven.pancake_other["path"][name], func, methods=["GET"])
        for name, func in oven.pancake_dough["PostAutoController"].items():
            self.app.add_api_route(oven.pancake_other["path"][name], func, methods=["POST"])
        for name, func in oven.pancake_dough["GetAutoController"].items():
            self.app.add_api_route(oven.pancake_other["path"][name], func, methods=["GET"])

    def loop_method(self):
        logger.info(f"启动服务 {self.service_title}，监听地址 {self.service_host}:{self.service_port}")
        uvicorn.run(self.app, host=self.service_host, port=self.service_port)
        logger.info("服务启动成功")

"""
    post 控制器装饰器
    用于定义 post 请求的控制器
    :param path: 控制器路径
    :param name: 控制器名称
    :return: 控制器实例
"""
def post_controller(path: str, name: str = None):
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        oven.pancake_other["path"][name] = path
        oven.pancake_dough["PostController"][name] = func
        logger.info(f"PostController {name} 已加入库")
        return func
    return decorator

"""
    get 控制器方法装饰器
    用于定义 get 请求的控制器方法
    :param path: 控制器路径
    :param name: 控制器名称
    :return: 控制器方法实例
"""
def get_controller(path: str, name: str = None):
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        oven.pancake_other["path"][name] = path
        oven.pancake_dough["GetController"][name] = func
        logger.info(f"GetController {name} 已加入库")
        return func
    return decorator

"""
    post 自动填充参数控制器方法装饰器
    用于定义 post 请求的控制器方法，自动填充参数
    :param path: 控制器路径
    :param name: 控制器名称
    :return: 控制器方法实例
"""
def post_auto_controller(path: str, name: str = None):
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        oven.pancake_other["path"][name] = path
        oven.pancake_dough["PostAutoController"][name] = func
        logger.info(f"PostAutoController {name} 已加入库")
        return func
    return decorator

"""
    get 自动填充参数控制器方法装饰器
    用于定义 get 请求的控制器方法，自动填充参数
    :param path: 控制器路径
    :param name: 控制器名称
    :return: 控制器方法实例
"""
def get_auto_controller(path: str, name: str = None):
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        oven.pancake_other["path"][name] = path
        oven.pancake_dough["GetAutoController"][name] = func
        logger.info(f"GetAutoController {name} 已加入库")
        return func
    return decorator
