"""Python → TypeScript литералы."""

from typing import Any


def to_ts(value: Any, indent: int = 0) -> str:
    """Рекурсивно конвертирует Python-значение в TS-литерал."""
    pad = " " * indent
    pad_inner = " " * (indent + 2)

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        if value == float("inf"):
            return "999999999"
        if value == float("-inf"):
            return "-999999999"
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    if isinstance(value, (list, tuple)):
        if not value:
            return "[]"
        items = [to_ts(v, indent + 2) for v in value]
        return "[\n" + ",\n".join(f"{pad_inner}{item}" for item in items) + f"\n{pad}]"

    if isinstance(value, dict):
        if not value:
            return "{}"
        items = []
        for k, v in value.items():
            if isinstance(k, str):
                key = f'"{k}"'
            else:
                key = str(k)
            items.append(f"{pad_inner}{key}: {to_ts(v, indent + 2)}")
        return "{\n" + ",\n".join(items) + f"\n{pad}}}"

    raise ValueError(f"Cannot serialize: {type(value)}")


def generate_header(source: str) -> str:
    """Генерирует шапку файла."""
    return (
        "// AUTO-GENERATED. DO NOT EDIT.\n"
        f"// Source: {source}\n"
        "// Run: python scripts/transform.py\n"
    )
