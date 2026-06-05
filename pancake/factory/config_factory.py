"""
配置工厂 — 统一管理所有配置源

配置优先级（从低到高）：
  1. 内置默认值 (settings.py)
  2. .env 文件
  3. YAML 配置文件
  4. JSON 配置文件
  5. XML <global> 配置
  6. 环境变量 (PANCAKE_*)

使用方法：
    factory = ConfigFactory()
    factory.load_defaults()
    factory.load_yaml("src/resource/yaml")
    factory.load_xml_global(xml_config)
    factory.load_env_vars()
    merged = factory.merge()
    value = factory.get("service.port")
"""

import json
import logging
import os
import re
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ConfigFactory:
    """配置工厂 — 统一管理所有配置源"""

    # 配置源优先级（值越大优先级越高）
    SOURCE_DEFAULTS = 0
    SOURCE_DOTENV = 1
    SOURCE_YAML = 2
    SOURCE_JSON = 3
    SOURCE_XML = 4
    SOURCE_ENV = 5

    def __init__(self):
        self._sources: dict[int, dict] = {}
        self._merged: dict = {}
        self._dirty = True
        self._validators: list[Callable] = []
        self._watcher = None

    # === 注册配置源 ===

    def register_source(self, priority: int, data: dict):
        """注册配置源"""
        if data:
            self._sources[priority] = data
            self._dirty = True

    # === 加载各配置源 ===

    def load_defaults(self):
        """加载内置默认值（从 settings.py）"""
        from pancake import settings
        defaults = {k: v for k, v in settings._DEFAULTS.items() if v is not None}
        self.register_source(self.SOURCE_DEFAULTS, defaults)

    def load_dotenv(self, path: str = ".env"):
        """加载 .env 文件"""
        if not os.path.exists(path):
            return
        try:
            from dotenv import dotenv_values
            env_data = dotenv_values(path)
            # 转换 KEY=value 为扁平配置
            config = {}
            for key, value in env_data.items():
                if value is not None:
                    config[key.lower().replace("_", ".")] = self._auto_convert(value)
            self.register_source(self.SOURCE_DOTENV, config)
            logger.debug(f"已加载 .env: {path}")
        except ImportError:
            logger.debug("python-dotenv 未安装，跳过 .env 加载")
        except Exception as e:
            logger.warning(f"加载 .env 失败: {e}")

    def load_yaml(self, dir_path: str):
        """加载目录下所有 YAML 文件"""
        if not os.path.isdir(dir_path):
            return
        try:
            import yaml
        except ImportError:
            logger.debug("pyyaml 未安装，跳过 YAML 加载")
            return

        data = {}
        for filename in sorted(os.listdir(dir_path)):
            if not filename.endswith(('.yaml', '.yml')):
                continue
            filepath = os.path.join(dir_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded = yaml.safe_load(f)
                    if loaded and isinstance(loaded, dict):
                        data.update(loaded)
            except Exception as e:
                logger.warning(f"加载 YAML 失败 {filepath}: {e}")

        if data:
            # 解析占位符
            data = self._resolve_placeholders(data)
            # 扁平化
            flat = self._flatten(data)
            self.register_source(self.SOURCE_YAML, flat)

    def load_json(self, dir_path: str):
        """加载目录下所有 JSON 文件"""
        if not os.path.isdir(dir_path):
            return

        data = {}
        for filename in sorted(os.listdir(dir_path)):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(dir_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if loaded and isinstance(loaded, dict):
                        data.update(loaded)
            except Exception as e:
                logger.warning(f"加载 JSON 失败 {filepath}: {e}")

        if data:
            flat = self._flatten(data)
            self.register_source(self.SOURCE_JSON, flat)

    def load_xml_global(self, xml_data: dict):
        """从 XML 解析结果加载全局配置"""
        config = xml_data.get("config", {})
        if config:
            self.register_source(self.SOURCE_XML, config)

        # 插件级配置也加载
        for plugin in xml_data.get("plugins", []):
            plugin_config = plugin.get("config", {})
            if plugin_config:
                existing = self._sources.get(self.SOURCE_XML, {})
                existing.update(plugin_config)
                self.register_source(self.SOURCE_XML, existing)

    def load_env_vars(self, prefix: str = "PANCAKE_"):
        """加载环境变量（PANCAKE_SERVICE_PORT -> service.port）"""
        config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower().replace("_", ".")
                config[config_key] = self._auto_convert(value)
        if config:
            self.register_source(self.SOURCE_ENV, config)

    def load_plugin_configs(self):
        """加载所有已安装插件的配置"""
        try:
            from importlib.metadata import entry_points
        except ImportError:
            return

        eps = entry_points(group="pancake.plugins")
        for ep in eps:
            try:
                plugin_cls = ep.load()
                module_name = plugin_cls.__module__
                module = __import__(module_name, fromlist=["__file__"])
                module_file = getattr(module, "__file__", None)
                if module_file:
                    config_dir = os.path.join(os.path.dirname(module_file), "config")
                    if os.path.isdir(config_dir):
                        self.load_yaml(config_dir)
                        logger.debug(f"已加载插件配置: {ep.name} -> {config_dir}")
            except Exception as e:
                logger.debug(f"加载插件配置失败 {ep.name}: {e}")

    # === 合并和查询 ===

    def merge(self) -> dict:
        """按优先级合并所有配置源"""
        if not self._dirty:
            return self._merged

        merged = {}
        for priority in sorted(self._sources.keys()):
            source = self._sources[priority]
            merged.update(source)

        self._merged = merged
        self._dirty = False

        # 同步到 oven.pancake_yaml
        try:
            from pancake import oven
            oven.pancake_yaml.update(merged)
        except ImportError:
            pass

        return merged

    def get(self, key: str, default=None):
        """获取配置值"""
        if self._dirty:
            self.merge()
        return self._merged.get(key, default)

    def get_nested(self, *keys, default=None):
        """嵌套获取：get_nested("mybatis", "database", "url")"""
        key = ".".join(keys)
        return self.get(key, default)

    def get_all(self, prefix: str = None) -> dict:
        """获取所有配置，可选按前缀过滤"""
        if self._dirty:
            self.merge()
        if prefix:
            return {k: v for k, v in self._merged.items() if k.startswith(prefix)}
        return dict(self._merged)

    def to_flat(self) -> dict:
        """导出为扁平化字典（兼容 oven.pancake_yaml）"""
        if self._dirty:
            self.merge()
        return dict(self._merged)

    # === 验证 ===

    def add_validator(self, validator: Callable[[dict], list[str]]):
        """添加配置验证器"""
        self._validators.append(validator)

    def validate(self) -> list[str]:
        """执行所有验证器，返回错误列表"""
        if self._dirty:
            self.merge()
        errors = []
        for validator in self._validators:
            try:
                errors.extend(validator(self._merged))
            except Exception as e:
                errors.append(f"验证器异常: {e}")
        return errors

    # === 热重载 ===

    def enable_hot_reload(self, interval: float = 5.0, yaml_dir: str = None, json_dir: str = None):
        """启用配置热重载"""
        from pancake.resource.config_watcher import ConfigWatcher
        self._watcher = ConfigWatcher(interval=interval)
        if yaml_dir:
            self._watcher.watch_dir(yaml_dir)
        if json_dir:
            self._watcher.watch_dir(json_dir)

        def on_change(changed_files):
            logger.info(f"配置文件变更: {changed_files}")
            self._dirty = True
            self.merge()

        self._watcher.on_change(on_change)
        self._watcher.start()

    def stop_hot_reload(self):
        """停止配置热重载"""
        if self._watcher:
            self._watcher.stop()

    # === 工具方法 ===

    @staticmethod
    def _auto_convert(value: str):
        """自动转换字符串值为 Python 类型"""
        if not isinstance(value, str):
            return value
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    @staticmethod
    def _flatten(data: dict, parent_key: str = '', sep: str = '.') -> dict:
        """扁平化嵌套字典"""
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(ConfigFactory._flatten(value, new_key, sep).items())
            else:
                items.append((new_key, value))
        return dict(items)

    @staticmethod
    def _resolve_placeholders(data: dict) -> dict:
        """解析 ${key.path} 占位符"""
        pattern = re.compile(r'\$\{([a-zA-Z0-9_.]+)}')

        def resolve(obj, resolving=None):
            if resolving is None:
                resolving = set()
            if isinstance(obj, dict):
                return {k: resolve(v, resolving) for k, v in obj.items()}
            if isinstance(obj, list):
                return [resolve(i, resolving) for i in obj]
            if isinstance(obj, str):
                for _ in range(10):
                    match = pattern.search(obj)
                    if not match:
                        break
                    key_path = match.group(1)
                    if key_path in resolving:
                        break
                    resolving.add(key_path)
                    keys = key_path.split('.')
                    value = data
                    try:
                        for k in keys:
                            value = value[k]
                    except (KeyError, TypeError):
                        value = match.group(0)
                    obj = obj.replace(match.group(0), str(value))
                    resolving.discard(key_path)
                return obj
            return obj

        return resolve(data)


# 模块级默认实例
_config_factory = ConfigFactory()


def get_config_factory() -> ConfigFactory:
    """获取全局配置工厂实例"""
    return _config_factory
