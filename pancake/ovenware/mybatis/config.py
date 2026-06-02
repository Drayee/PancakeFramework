"""
MyBatis 配置加载
从 YAML 读取数据库配置
"""

import logging
import os

from pancake import oven

logger = logging.getLogger(__name__)

def _default_db_url():
    from pancake.settings import get_path
    return f"sqlite:///{os.path.join(get_path('db_dir'), 'app.db')}"

_DEFAULT_CONFIG = {
    "url": None,  # 运行时由 _default_db_url() 提供
    "min_size": 1,
    "max_size": 5,
}


def load_config() -> dict:
    """加载 mybatis 配置"""
    config = {}

    # 从 pancake_yaml 读取
    for key, default in _DEFAULT_CONFIG.items():
        yaml_key = f"mybatis.database.{key}"
        value = oven.pancake_yaml.get(yaml_key, default)
        if value is None and key == "url":
            value = _default_db_url()
        config[key] = value

    logger.info(f"MyBatis 配置: url={config['url']}")
    return config
