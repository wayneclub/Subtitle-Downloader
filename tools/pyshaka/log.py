import sys
import logging
import datetime
from pathlib import Path


def setup_logger(name: str, write_to_file: bool = False) -> logging.Logger:
    formatter = logging.Formatter('%(message)s')
    log_time = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    app_path = Path(__file__).parent.parent.parent
    log_folder_path = app_path / 'logs'
    if log_folder_path.exists() is False:
        log_folder_path.mkdir()

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    lt = logging.getLogger(f'{name}')
    lt.setLevel(logging.INFO)
    lt.addHandler(ch)
    if write_to_file:
        log_file_path = log_folder_path / f'{name}-{log_time}.log'
        fh = logging.FileHandler(
            log_file_path.resolve().as_posix(), encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        lt.addHandler(fh)
        lt.info(f'log file -> {log_file_path}')
    return lt


log = setup_logger('pyshaka')
