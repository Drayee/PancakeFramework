# CLI 参考

Pancake 提供命令行工具管理项目。

## 命令

| 命令 | 说明 |
|------|------|
| `pancake version` | 显示框架版本 |
| `pancake init` | 在当前目录初始化项目 |
| `pancake create <name>` | 在子目录创建新项目 |
| `pancake run` | 运行项目 |
| `pancake check` | 检查项目结构和环境 |
| `pancake build` | 打包项目为 wheel |
| `pancake plugin list` | 列出可用插件及状态 |
| `pancake plugin add <name>` | 添加插件到 pancake.xml |
| `pancake config show` | 显示当前配置（敏感值脱敏） |
| `pancake audit` | 审核 src/ 代码质量 |
| `pancake update` | 更新 pancake_framework 包 |
| `pancake install` | 安装缺失依赖 |

## 使用示例

### 创建并运行项目

```bash
pancake create myapp
cd myapp
pip install pancake_framework
pancake run
```

### 在当前目录初始化

```bash
mkdir myapp && cd myapp
pancake init
pip install pancake_framework
python main.py
```

### 插件管理

```bash
# 列出所有插件
pancake plugin list

# 添加插件到 pancake.xml
pancake plugin add redis_cache
```

### 代码审核

```bash
pancake audit
```

检查 `src/` 下所有 `.py` 文件的非声明语句。在 Pancake 中，源文件应主要包含 import、类定义和函数定义。

### 显示配置

```bash
pancake config show
```

显示所有 YAML 和 XML 配置，敏感值（密码、令牌）自动脱敏。
