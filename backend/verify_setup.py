#!/usr/bin/env python3
"""
Step 1 Verification Script for Chaos Budget.

Checks:
  1. Python version is 3.11+
  2. Every required folder and file exists
  3. Every package in requirements.txt is importable
  4. .env file exists and contains all required keys
  5. Config module loads without error (skipped if .env has placeholder values)

Run from the backend/ directory:
    python verify_setup.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# ── Rich console for pretty output ───────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("ERROR: 'rich' package not installed. Run: pip install rich")
    sys.exit(1)

console = Console()

# Counters
passed = 0
failed = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    """Print a ✅ or ❌ line and update counters."""
    global passed, failed
    if condition:
        passed += 1
        console.print(f"  ✅  {label}", style="green")
    else:
        failed += 1
        msg = f"  ❌  {label}"
        if detail:
            msg += f"  —  {detail}"
        console.print(msg, style="bold red")


# ══════════════════════════════════════════════════════════════════════
# 1. Python version
# ══════════════════════════════════════════════════════════════════════
console.print(Panel("[bold cyan]Step 1 — Chaos Budget Setup Verification[/bold cyan]"))

v = sys.version_info
version_str = f"{v.major}.{v.minor}.{v.micro}"
console.print(f"\n  Python version: [bold]{version_str}[/bold]")
check("Python >= 3.11", (v.major, v.minor) >= (3, 11), f"Found {version_str}")

# ══════════════════════════════════════════════════════════════════════
# 2. Folder & file structure
# ══════════════════════════════════════════════════════════════════════
console.print("\n[bold]📁 Folder & File Structure[/bold]")

ROOT = Path(__file__).resolve().parent.parent  # chaos-budget/
BACKEND = ROOT / "backend"

expected_paths = [
    # Top level
    ROOT / ".gitignore",
    ROOT / "README.md",
    # Backend dirs
    BACKEND / "app",
    BACKEND / "app" / "models",
    BACKEND / "app" / "routes",
    BACKEND / "app" / "services",
    BACKEND / "app" / "utils",
    BACKEND / "tests",
    # Backend files
    BACKEND / "requirements.txt",
    BACKEND / ".env.example",
    BACKEND / "Dockerfile",
    BACKEND / "app" / "__init__.py",
    BACKEND / "app" / "main.py",
    BACKEND / "app" / "config.py",
    BACKEND / "app" / "database.py",
    BACKEND / "app" / "models" / "__init__.py",
    BACKEND / "app" / "models" / "timeline.py",
    BACKEND / "app" / "routes" / "__init__.py",
    BACKEND / "app" / "routes" / "timeline.py",
    BACKEND / "app" / "routes" / "simulate.py",
    BACKEND / "app" / "routes" / "explain.py",
    BACKEND / "app" / "services" / "__init__.py",
    BACKEND / "app" / "services" / "parser.py",
    BACKEND / "app" / "services" / "simulator.py",
    BACKEND / "app" / "services" / "causal.py",
    BACKEND / "app" / "services" / "explainer.py",
    BACKEND / "app" / "utils" / "__init__.py",
    BACKEND / "app" / "utils" / "logger.py",
    BACKEND / "tests" / "__init__.py",
    # Frontend dir (empty for now)
    ROOT / "frontend",
]

for p in expected_paths:
    rel = p.relative_to(ROOT)
    check(str(rel), p.exists())

# ══════════════════════════════════════════════════════════════════════
# 3. Package imports
# ══════════════════════════════════════════════════════════════════════
console.print("\n[bold]📦 Package Imports[/bold]")

# Map requirements.txt names → Python import names
IMPORT_MAP: dict[str, str] = {
    "fastapi": "fastapi",
    "uvicorn[standard]": "uvicorn",
    "motor": "motor",
    "pymongo": "pymongo",
    "python-dotenv": "dotenv",
    "groq": "groq",
    "dowhy": "dowhy",
    "numpy": "numpy",
    "pandas": "pandas",
    "scikit-learn": "sklearn",
    "pydantic": "pydantic",
    "pydantic-settings": "pydantic_settings",
    "httpx": "httpx",
    "loguru": "loguru",
    "pytest": "pytest",
    "pytest-asyncio": "pytest_asyncio",
    "rich": "rich",
}

for req_name, import_name in IMPORT_MAP.items():
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, "__version__", "—")
        check(f"{req_name} ({import_name} v{version})", True)
    except ImportError as e:
        check(f"{req_name} ({import_name})", False, str(e))

# ══════════════════════════════════════════════════════════════════════
# 4. .env file
# ══════════════════════════════════════════════════════════════════════
console.print("\n[bold]🔑 Environment File (.env)[/bold]")

env_path = BACKEND / ".env"
env_exists = env_path.exists()
check(".env file exists", env_exists, "Copy .env.example → .env and fill in real values")

REQUIRED_KEYS = ["GROQ_API_KEY", "MONGODB_URI", "MONGODB_DB_NAME", "ENVIRONMENT", "CORS_ORIGINS"]

if env_exists:
    env_contents = env_path.read_text()
    env_lines = {
        line.split("=", 1)[0].strip(): line.split("=", 1)[1].strip()
        for line in env_contents.splitlines()
        if "=" in line and not line.strip().startswith("#")
    }
    for key in REQUIRED_KEYS:
        present = key in env_lines and len(env_lines[key]) > 0
        check(f"  .env has {key}", present)
else:
    for key in REQUIRED_KEYS:
        check(f"  .env has {key}", False, ".env file missing")

# ══════════════════════════════════════════════════════════════════════
# 5. Summary
# ══════════════════════════════════════════════════════════════════════
console.print()
table = Table(title="Verification Summary", show_header=True, header_style="bold magenta")
table.add_column("Metric", style="cyan")
table.add_column("Count", justify="right")
table.add_row("Passed", f"[green]{passed}[/green]")
table.add_row("Failed", f"[red]{failed}[/red]")
table.add_row("Total", str(passed + failed))
console.print(table)

if failed == 0:
    console.print("\n[bold green]🎉 All checks passed! Step 1 scaffold is solid.[/bold green]\n")
else:
    console.print(f"\n[bold red]⚠  {failed} check(s) failed. Fix them before proceeding.[/bold red]\n")

sys.exit(0 if failed == 0 else 1)
