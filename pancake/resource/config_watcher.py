"""
配置热重载
监听 YAML/JSON 配置文件变更，自动重新加载
"""

import logging
import os
import threading
import time

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """配置文件变更监听器 — 基于轮询，无需额外依赖"""

    def __init__(self, interval: float = 5.0):
        self._interval = interval
        self._watching = False
        self._thread: threading.Thread | None = None
        self._watched_files: dict[str, float] = {}
        self._callbacks: list = []

    def watch_dir(self, dir_path: str) -> None:
        """监听目录下的 .yaml/.yml/.json 文件"""
        if not os.path.exists(dir_path):
            return
        for filename in os.listdir(dir_path):
            if filename.endswith(('.yaml', '.yml', '.json')):
                filepath = os.path.join(dir_path, filename)
                self._watched_files[filepath] = os.path.getmtime(filepath)

    def on_change(self, callback) -> None:
        """注册变更回调"""
        self._callbacks.append(callback)

    def _check_changes(self) -> list[str]:
        """检查文件是否有变更，返回变更的文件列表"""
        changed = []
        for filepath, last_mtime in list(self._watched_files.items()):
            if not os.path.exists(filepath):
                continue
            current_mtime = os.path.getmtime(filepath)
            if current_mtime > last_mtime:
                self._watched_files[filepath] = current_mtime
                changed.append(filepath)
        return changed

    def _poll_loop(self) -> None:
        """轮询循环"""
        while self._watching:
            time.sleep(self._interval)
            changed = self._check_changes()
            if changed:
                logger.info(f"检测到配置变更: {changed}")
                for callback in self._callbacks:
                    try:
                        callback(changed)
                    except Exception as e:
                        logger.error(f"配置重载回调异常: {e}")

    def start(self) -> None:
        """启动监听"""
        if self._watching:
            return
        self._watching = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"配置热重载已启动，监听 {len(self._watched_files)} 个文件，轮询间隔 {self._interval}s")

    def stop(self) -> None:
        """停止监听"""
        self._watching = False
        if self._thread:
            self._thread.join(timeout=self._interval + 1)
            self._thread = None
        logger.info("配置热重载已停止")


# 模块级默认实例
_watcher = ConfigWatcher()


def start_config_watcher(interval: float = 5.0) -> ConfigWatcher:
    """启动配置热重载"""
    from pancake.settings import get_path

    _watcher._interval = interval

    # 监听 YAML 和 JSON 配置目录
    yaml_dir = get_path("yaml_dir")
    json_dir = get_path("json_dir")

    if yaml_dir:
        _watcher.watch_dir(yaml_dir)
    if json_dir:
        _watcher.watch_dir(json_dir)

    def reload_config(changed_files):
        """重新加载配置到 settings

        使用 settings.replace() 替换而非 merge，
        确保从配置文件中删除的 key 不会残留。
        """
        from pancake import settings
        from pancake.resource import yml, json

        # 收集所有配置源
        all_new_data = {}

        # 重新加载 YAML
        yaml_data = yml.yaml_init()
        if yaml_data:
            all_new_data.update(yaml_data)

        # 重新加载 JSON
        json_data = json.json_init()
        if json_data:
            all_new_data.update(json_data)

        # 替换配置（清除旧 key），但保留 XML 基础配置
        from pancake.resource import xml_config
        xml_config_data = xml_config.load_xml().get("config", {})
        xml_config_data.update(all_new_data)
        settings.replace(xml_config_data)
        logger.info(f"配置已热重载 ({len(all_new_data)} 个 key)")

    _watcher.on_change(reload_config)
    _watcher.start()
    return _watcher


def stop_config_watcher() -> None:
    """停止配置热重载"""
    _watcher.stop()
