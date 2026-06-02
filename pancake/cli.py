"""
Pancake CLI - 命令行工具
支持 create / check / run / build 等子命令
"""

import argparse
import os
import sys
import shutil
import subprocess


def cmd_create(args):
    """创建新项目"""
    name = args.name
    project_dir = os.path.join(os.getcwd(), name)

    if os.path.exists(project_dir):
        print(f"错误: 目录 '{name}' 已存在")
        sys.exit(1)

    print(f"创建项目: {name}")

    # 创建目录结构
    dirs = [
        os.path.join(project_dir, "src", "resource", "yaml"),
        os.path.join(project_dir, "src", "resource", "json"),
        os.path.join(project_dir, "src", "mapper"),
        os.path.join(project_dir, "src", "controller"),
    ]
    for d in dirs:
        os.makedirs(d)

    # 创建 main.py
    with open(os.path.join(project_dir, "main.py"), "w", encoding="utf-8") as f:
        f.write('import pancake\n\npancake.run()\n')

    # 创建 pancake.xml
    with open(os.path.join(project_dir, "pancake.xml"), "w", encoding="utf-8") as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<pancake>
    <global>
        <service.title>''' + name + '''</service.title>
        <service.version>1.0.0</service.version>
        <service.host>127.0.0.1</service.host>
        <service.port>8080</service.port>
    </global>
    <plugins>
        <plugin name="embed" init-order="0"/>
        <plugin name="mybatis" init-order="1"/>
        <plugin name="web" init-order="2"/>
    </plugins>
</pancake>
''')

    # 创建 service.yaml
    with open(os.path.join(project_dir, "src", "resource", "yaml", "service.yaml"), "w", encoding="utf-8") as f:
        f.write('''service:
  title: ''' + name + '''
  version: 1.0.0
  host: 127.0.0.1
  port: 8080
''')

    # 创建 pyproject.toml
    with open(os.path.join(project_dir, "pyproject.toml"), "w", encoding="utf-8") as f:
        f.write('''[tool.poetry]
name = "''' + name + '''"
version = "0.1.0"
description = "A Pancake framework project"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.13"
pancake = "*"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
''')

    print(f"项目 '{name}' 创建成功!")
    print(f"  cd {name}")
    print(f"  pip install pancake")
    print(f"  python main.py")


def cmd_check(args):
    """检查项目结构和环境"""
    print("检查项目结构...")

    errors = []
    warnings = []

    # 检查 main.py
    if not os.path.exists("main.py"):
        errors.append("缺少 main.py")
    else:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "import pancake" not in content:
                warnings.append("main.py 中未找到 'import pancake'")

    # 检查 pancake.xml
    if not os.path.exists("pancake.xml"):
        warnings.append("缺少 pancake.xml（可选，用于插件配置）")

    # 检查 src 目录
    if not os.path.isdir("src"):
        errors.append("缺少 src 目录")
    else:
        yaml_dir = os.path.join("src", "resource", "yaml")
        if not os.path.isdir(yaml_dir):
            warnings.append(f"缺少 {yaml_dir} 目录")
        else:
            yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
            if not yaml_files:
                warnings.append(f"{yaml_dir} 中没有 YAML 配置文件")

    # 检查 pancake 是否安装
    try:
        import pancake  # noqa: F401
        print("  [OK] pancake 已安装")
    except ImportError:
        errors.append("pancake 未安装，请运行: pip install pancake")

    # 输出结果
    if errors:
        print("\n错误:")
        for e in errors:
            print(f"  [ERROR] {e}")

    if warnings:
        print("\n警告:")
        for w in warnings:
            print(f"  [WARN] {w}")

    if not errors and not warnings:
        print("  项目结构正常!")

    return len(errors) == 0


def cmd_run(args):
    """运行项目"""
    if not os.path.exists("main.py"):
        print("错误: 当前目录没有 main.py，请在项目根目录运行")
        sys.exit(1)

    print("启动 Pancake 项目...")
    import pancake
    pancake.run()


def cmd_build(args):
    """打包项目为 wheel"""
    if not os.path.exists("pyproject.toml"):
        print("错误: 当前目录没有 pyproject.toml")
        sys.exit(1)

    print("打包项目...")
    result = subprocess.run(
        [sys.executable, "-m", "poetry", "build"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("打包成功!")
        print(result.stdout)
    else:
        print("打包失败:")
        print(result.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="pancake",
        description="Pancake Framework - 命令行工具",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # create
    create_parser = subparsers.add_parser("create", help="创建新项目")
    create_parser.add_argument("name", help="项目名称")

    # check
    subparsers.add_parser("check", help="检查项目结构和环境")

    # run
    subparsers.add_parser("run", help="运行项目")

    # build
    subparsers.add_parser("build", help="打包项目为 wheel")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "create": cmd_create,
        "check": cmd_check,
        "run": cmd_run,
        "build": cmd_build,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
