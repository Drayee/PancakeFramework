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
    """Maven-like 包管理器 — 无硬编码插件映射

    依赖信息完全来自 XML <dependencies> 配置：
    - groupId="io.pancake"：框架插件，从插件的 requires 声明获取包名
    - groupId="pypi"：第三方包，artifactId 即为 pip 包名
    """

    def __init__(self, dependencies: list[dict]):
        """
        Args:
            dependencies: 从 XML 解析的依赖列表
                [{"groupId": "io.pancake", "artifactId": "embed", "requires": [...]},
                 {"groupId": "pypi", "artifactId": "requests"}, ...]
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

        cmd = [sys.executable, "-m", "pip", "install"] + missing
        logger.info(f"安装包: {cmd}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"安装失败: {result.stderr}")
                return False
            logger.info(f"安装成功: {missing}")
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

            if result["status"] == "ok":
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
        requires = dep.get("requires", [])

        result = {
            "name": artifact_id,
            "groupId": group_id,
            "optional": optional,
            "status": "unknown",
        }

        if group_id == "pypi":
            # 第三方包：artifactId 即为 pip 包名
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

        elif requires:
            # 有 requires 声明的插件：检查 requires 中的包
            missing = []
            for mod in requires:
                try:
                    __import__(mod)
                except ImportError:
                    missing.append(mod)

            if missing:
                result["status"] = "optional_missing" if optional else "missing"
                result["missing_packages"] = missing
            else:
                result["status"] = "ok"

        else:
            # 无 requires 声明：视为内建，直接通过
            result["status"] = "ok"

        return result

    def resolve(self, dep: dict) -> tuple[list[str], Optional[str]]:
        """解析依赖 -> (检查模块列表, pip extras名)"""
        return dep.get("requires", []), None


def plugins_to_dependencies(plugins: list[dict]) -> list[dict]:
    """旧 <plugins> 格式转为 <dependencies> 格式"""
    return [
        {"groupId": "io.pancake", "artifactId": p["name"]}
        for p in plugins
    ]
