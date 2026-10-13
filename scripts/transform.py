#!/usr/bin/env python3
"""
Трансформер: Python → TypeScript.

Запуск:
    python scripts/transform.py

Что делает:
    1. Читает core/constants.py
    2. Генерирует frontend/src/generated/constants.ts
"""

import sys
from pathlib import Path

# Корень репо (scripts/ → корень)
REPO_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = REPO_ROOT

# Добавляем корень в sys.path, чтобы импортировать core.constants
sys.path.insert(0, str(BACKEND_ROOT))

from scripts.parsers.constants_parser import parse_constants
from scripts.generators.ts_generator import to_ts, generate_header

FRONTEND_DIR = REPO_ROOT / "frontend"
OUTPUT_DIR = FRONTEND_DIR / "src" / "generated"


def generate_constants() -> None:
    """Генерирует frontend/src/generated/constants.ts."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        constants = parse_constants("core.constants")
    except Exception as e:
        print(f"⚠️  Cannot parse core.constants: {e}")
        print("   Creating empty constants.ts")
        constants = {}

    lines = [generate_header("core/constants.py"), ""]

    for name, value in sorted(constants.items()):
        try:
            ts_value = to_ts(value)
            lines.append(f"export const {name} = {ts_value} as const;")
            lines.append("")
        except Exception as e:
            print(f"⚠️  Skip {name}: {e}")

    output = OUTPUT_DIR / "constants.ts"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Generated: {output}")


def main() -> None:
    print("🔄 Transform: Python → TypeScript")
    print()
    generate_constants()
    print()
    print("✅ Done. Design by Expo")


if __name__ == "__main__":
    main()
