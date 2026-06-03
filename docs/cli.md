# CLI Reference

Pancake provides a command-line tool for project management.

## Commands

| Command | Description |
|---------|-------------|
| `pancake version` | Show framework version |
| `pancake init` | Initialize project in current directory |
| `pancake create <name>` | Create a new project in a subdirectory |
| `pancake run` | Run the project |
| `pancake check` | Check project structure and environment |
| `pancake build` | Package project as wheel |
| `pancake plugin list` | List available plugins and their status |
| `pancake plugin add <name>` | Add a plugin to pancake.xml |
| `pancake config show` | Show current configuration (sensitive values masked) |
| `pancake audit` | Audit src/ code quality |
| `pancake update` | Update pancake_framework package |
| `pancake install` | Install missing dependencies |

## Usage Examples

### Create and Run a Project

```bash
pancake create myapp
cd myapp
pip install pancake_framework
pancake run
```

### Initialize in Current Directory

```bash
mkdir myapp && cd myapp
pancake init
pip install pancake_framework
python main.py
```

### Plugin Management

```bash
# List all plugins
pancake plugin list

# Add a plugin to pancake.xml
pancake plugin add redis_cache
```

### Code Audit

```bash
pancake audit
```

Checks all `.py` files in `src/` for non-declaration statements. In Pancake, source files should primarily contain imports, class definitions, and function definitions.

### Show Configuration

```bash
pancake config show
```

Displays all YAML and XML configuration with sensitive values (passwords, tokens) automatically masked.
