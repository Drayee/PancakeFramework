"""
烤箱仓库
"""

import importlib
import pkgutil

# 当前包下的所有模块
for _, module_name, _ in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f".{module_name}", __name__)

    for attr_name in dir(module):
        if not attr_name.startswith('_'):
            attr = getattr(module, attr_name)
            globals()[attr_name] = attr