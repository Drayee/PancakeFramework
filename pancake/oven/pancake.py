"""
Pancake 配置存储
管理框架配置数据：YAML、JSON、XML
类/实例/运行时数据已迁移到 registry.py
"""


class PancakeConfig:
    """Pancake 配置存储"""

    def __init__(self):
        self.json: dict = {}
        self.yaml: dict = {}
        self.xml: dict = {}

    def reset(self):
        """重置所有配置（用于测试）"""
        for d in (self.json, self.yaml, self.xml):
            d.clear()


# 向后兼容的模块级默认实例
_config = PancakeConfig()

pancake_json = _config.json
pancake_yaml = _config.yaml
pancake_xml = _config.xml


def create_config() -> PancakeConfig:
    """创建新的独立配置（用于测试）"""
    return PancakeConfig()
