"""Парсер констант из core/constants.py."""

import importlib
from typing import Any


def is_serializable(value: Any) -> bool:
    """Проверяет, можно ли сериализовать значение в JSON/TS."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return True
    if isinstance(value, (list, tuple)):
        return all(is_serializable(v) for v in value)
    if isinstance(value, dict):
        return all(
            isinstance(k, (str, int, float)) and is_serializable(v)
            for k, v in value.items()
        )
    return False


def parse_constants(module_path: str = "core.constants") -> dict[str, Any]:
    """
    Импортирует модуль и возвращает только сериализуемые UPPER_CASE константы.
    """
    module = importlib.import_module(module_path)
    result: dict[str, Any] = {}

    for name in dir(module):
        if name.startswith("_"):
            continue
        if not name.isupper():
            continue

        value = getattr(module, name)
        if is_serializable(value):
            result[name] = value

    return result 
