# 16. CUI Plugin — CLI Interface

[← Previous](15-remote.md) | [Next →](17-gui.md)

---

## Overview

`pancake-cui` provides a Click-powered CLI framework with command groups, colored output, progress bars, and interactive input.

## Enable

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>cui</artifactId>
</dependency>
```

## Configuration

```yaml
client:
  type: cui
  cui:
    app_name: mycli
    version: 1.0.0
```

## Defining Commands

```python
@cui_command()
@cui_option("--name", prompt="Your name", help="Your name")
def greet(name: str):
    """Greet someone"""
    cui_success(f"Hello, {name}!")

@cui_group()
class DatabaseCommands:
    """Database management commands"""

@cui_command(group="database")
@cui_option("--force", is_flag=True, help="Force reset")
def migrate(force: bool):
    """Run database migration"""
    if force:
        cui_warning("Force reset!")
    cui_info("Migration complete")
```

## Output Utilities

```python
cui_info("Processing...")        # Blue [INFO]
cui_success("Done!")             # Green [OK]
cui_warning("Careful!")          # Yellow [WARN]
cui_error("Failed!")             # Red [ERROR]
cui_print("Custom", fg="cyan")  # Custom color

name = cui_prompt("Enter name")          # Interactive input
confirm = cui_confirm("Are you sure?")   # Confirmation

with cui_progress(100, "Downloading") as p:
    for i in range(100):
        p.update(1)
```

---

[← Previous](15-remote.md) | [Next →](17-gui.md)
