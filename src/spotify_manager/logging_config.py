import logging
import os
from pathlib import Path

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "logs/app.log"
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
THIRD_PARTY_LOG_LEVELS = {
    "spotipy": logging.WARNING,
    "urllib3": logging.WARNING,
}


def configure_logging() -> None:
    """Настроить стандартное логирование приложения."""
    log_level_name = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    log_file = _get_log_file_path()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    _configure_third_party_logging()


def _configure_third_party_logging() -> None:
    """Приглушить подробные логи библиотек."""
    for logger_name, log_level in THIRD_PARTY_LOG_LEVELS.items():
        logging.getLogger(logger_name).setLevel(log_level)


def _get_log_file_path() -> Path:
    """Вернуть путь к лог-файлу относительно проекта, если он не абсолютный."""
    log_file = Path(os.getenv("LOG_FILE", DEFAULT_LOG_FILE))
    if log_file.is_absolute():
        return log_file

    return PROJECT_ROOT / log_file
