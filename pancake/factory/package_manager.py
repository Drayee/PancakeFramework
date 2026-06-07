"""
Maven-like 包管理器
解析 XML <dependencies>，检查缺失依赖，自动 pip install。

使用方法：
    pm = PackageManager(dependencies)
    missing = pm.check_all()
    if missing:
        pm.install_missing(missing)
    pm.print_report()
"""

import logging
import subprocess
import sys
from importlib.metadata import version as get_version
from typing import Optional

logger = logging.getLogger(__name__)


class PackageManager:
    """Maven-like 包管理器"""

    # 插件名 -> 需要 import 检查的 Python 包
    PLUGIN_IMPORTS: dict[str, list[str]] = {
        "embed": [],
        "web": ["fastapi", "uvicorn"],
        "mybatis": ["databases", "aiosqlite"],
        "redis": ["redis"],
        "ai_model": ["openai"],
        "langgraph": ["langgraph"],
        "broker": [],
        "lifecycle": [],
        "remote": ["aiohttp"],
        "cui": ["click"],
        "gui": ["flet"],
        "external_plugin": [],
    }

    # 插件名 -> pip install pancake_framework[extras] 的 extras 名
    PLUGIN_PIP_EXTRAS: dict[str, str] = {
        "web": "web",
        "mybatis": "mybatis",
        "redis": "redis",
        "ai_model": "ai",
        "langgraph": "langgraph",
        "cui": "cui",
        "gui": "gui",
        "remote": "http",
    }

    # 已知的内建插件（不需要 pip install，只控制是否加载）
    BUILTIN_PLUGINS: set[str] = {
        "embed", "broker", "lifecycle", "external_plugin",
    }

    def __init__(self, dependencies: list[dict]):
        """
        Args:
            dependencies: 从 XML 解析的依赖列表
                [{"groupId": "io.pancake", "artifactId": "web"}, ...]
        """
        self.deps = dependencies
        self.results: list[dict] = []  # 检查结果

    def check_all(self) -> list[str]:
        """检查所有依赖，返回缺失的包列表"""
        missing = []

        for dep in self.deps:
            result = self._check_one(dep)
            self.results.append(result)
            if result["status"] == "missing":
                missing.extend(result["missing_packages"])

        return missing

    def install_missing(self, missing: list[str]) -> bool:
        """自动 pip install 缺失的包"""
        if not missing:
            return True

        # 收集需要的 extras
        extras_to_install = set()
        packages_to_install = []

        for pkg in missing:
            # 检查是否是某个 plugin extra 包含的
            found_extra = False
            for plugin, imports in self.PLUGIN_IMPORTS.items():
                if pkg in imports and plugin in self.PLUGIN_PIP_EXTRAS:
                    extras_to_install.add(self.PLUGIN_PIP_EXTRAS[plugin])
                    found_extra = True
                    break
            if not found_extra:
                packages_to_install.append(pkg)

        # 安装 extras
        if extras_to_install:
            extras_str = ",".join(extras_to_install)
            cmd = [sys.executable, "-m", "pip", "install", f"pancake_framework[{extras_str}]"]
            logger.info(f"安装 extras: {cmd}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    logger.error(f"安装失败: {result.stderr}")
                    return False
                logger.info(f"安装成功: pancake_framework[{extras_str}]")
            except subprocess.TimeoutExpired:
                logger.error("安装超时")
                return False

        # 安装独立包
        if packages_to_install:
            cmd = [sys.executable, "-m", "pip", "install"] + packages_to_install
            logger.info(f"安装包: {cmd}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    logger.error(f"安装失败: {result.stderr}")
                    return False
                logger.info(f"安装成功: {packages_to_install}")
            except subprocess.TimeoutExpired:
                logger.error("安装超时")
                return False

        return True

    def print_report(self):
        """打印依赖检查报告"""
        if not self.results:
            self.check_all()

        print("\n检查依赖...")
        for result in self.results:
            name = result["name"]
            group = result["groupId"]

            if result["status"] == "builtin":
                print(f"  [OK] {name} (内建)")
            elif result["status"] == "ok":
                version = result.get("version", "")
                version_str = f" ({version})" if version else ""
                print(f"  [OK] {name}{version_str}")
            elif result["status"] == "missing":
                pkgs = ", ".join(result["missing_packages"])
                print(f"  [FAIL] {name} -- 缺少: {pkgs}")
            elif result["status"] == "optional_missing":
                print(f"  [WARN] {name} (可选，未安装)")
            else:
                print(f"  [?] {name} -- {result.get('error', '未知')}")
        print()

    def _check_one(self, dep: dict) -> dict:
        """检查单个依赖"""
        group_id = dep.get("groupId", "io.pancake")
        artifact_id = dep.get("artifactId", "")
        optional = dep.get("optional", False)

        result = {
            "name": artifact_id,
            "groupId": group_id,
            "optional": optional,
            "status": "unknown",
        }

        if group_id == "io.pancake":
            # 框架插件
            if artifact_id in self.BUILTIN_PLUGINS:
                result["status"] = "builtin"
                return result

            imports = self.PLUGIN_IMPORTS.get(artifact_id, [])
            if not imports:
                result["status"] = "ok"
                return result

            missing = []
            for mod in imports:
                try:
                    __import__(mod)
                except ImportError:
                    missing.append(mod)

            if missing:
                result["status"] = "optional_missing" if optional else "missing"
                result["missing_packages"] = missing
            else:
                result["status"] = "ok"

        elif group_id == "pypi":
            # 第三方包
            pkg_name = artifact_id
            try:
                ver = get_version(pkg_name)
                result["status"] = "ok"
                result["version"] = ver
            except Exception:
                if optional:
                    result["status"] = "optional_missing"
                else:
                    result["status"] = "missing"
                    result["missing_packages"] = [pkg_name]

        else:
            result["status"] = "unknown"
            result["error"] = f"未知 groupId: {group_id}"

        return result

    def resolve(self, dep: dict) -> tuple[list[str], Optional[str]]:
        """解析依赖 -> (检查模块列表, pip extras名)"""
        group_id = dep.get("groupId", "io.pancake")
        artifact_id = dep.get("artifactId", "")

        if group_id == "io.pancake":
            imports = self.PLUGIN_IMPORTS.get(artifact_id, [])
            extras = self.PLUGIN_PIP_EXTRAS.get(artifact_id)
            return imports, extras
        elif group_id == "pypi":
            return [artifact_id], None
        return [], None


def plugins_to_dependencies(plugins: list[dict]) -> list[dict]:
    """旧 <plugins> 格式转为 <dependencies> 格式"""
    return [
        {"groupId": "io.pancake", "artifactId": p["name"]}
        for p in plugins
    ]
