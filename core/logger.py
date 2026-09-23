"""Логгер. Пишет в stdout Render. Подробный, для отладки."""

import logging
import sys


class CustomFormatter(logging.Formatter):
    """Формат логов с эмодзи и коротким временем."""

    FORMATS = {
        logging.DEBUG: "🔍 [%(asctime)s] %(message)s",
        logging.INFO: "✅ [%(asctime)s] %(message)s",
        logging.WARNING: "⚠️ [%(asctime)s] %(message)s",
        logging.ERROR: "❌ [%(asctime)s] %(message)s",
        logging.CRITICAL: "🚨 [%(asctime)s] %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "ℹ️ [%(asctime)s] %(message)s")
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logger(name: str = "indycarts") -> logging.Logger:
    """Создаёт логгер с подробным форматом."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)  # ← DEBUG, чтобы видеть ВСЁ

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())

    logger.addHandler(handler)
    logger.propagate = False

    return logger 
